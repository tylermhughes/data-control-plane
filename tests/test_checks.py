"""Automated quality checks on real files (local), S3 (stubbed), statuses and decisions."""

import hashlib
import io
from pathlib import Path
from typing import Any

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checks import storage
from app.models import Event
from app.worker.__main__ import run_once
from tests.helpers import Headers, Setup, post_ok, write_jsonl

SCHEMA = {
    "type": "object",
    "required": ["id", "package_type"],
    "properties": {
        "id": {"type": "string"},
        "package_type": {"enum": ["box", "mailer", "shrink_wrapped"]},
        "severity": {"type": "integer", "minimum": 1, "maximum": 5},
    },
}
RULES = [
    {"metric": "schema_valid_rate", "operator": ">=", "threshold": 0.95},
    {"metric": "duplicate_rate", "operator": "<=", "threshold": 0.05},
    {"metric": "agreement", "operator": ">=", "threshold": 0.85},
]


def records(n: int, prefix: str = "r", **extra: Any) -> list[dict[str, Any]]:
    types = ["box", "mailer", "shrink_wrapped"]
    zones = ["induct", "sort"]
    return [
        {"id": f"{prefix}{i}", "package_type": types[i % 3], "zone": zones[i % 2], "severity": 2}
        | extra
        for i in range(n)
    ]


class Checked:
    """A project whose request uses a spec version with a record schema and rules."""

    def __init__(self, client: TestClient, admin: Headers, data_dir: Path, db: Session) -> None:
        self.s = Setup(client, admin)
        self.client, self.admin, self.data_dir, self.db = client, admin, data_dir, db
        v2 = post_ok(
            client,
            f"/v1/specs/{self.s.spec_id}/versions",
            admin,
            {"record_schema": SCHEMA, "acceptance_rules": RULES},
        )
        post_ok(
            client, f"/v1/specs/{self.s.spec_id}/versions/2/approve", admin, {"approved_by": "PM"}
        )
        req = self.s.open_request(spec_version_id=v2["id"])
        alloc = self.s.allocate(req["id"], "Surge")
        self.alloc = self.s.act("allocations", alloc["id"], "activate").json()

    def file(self, name: str, rows: list[dict[str, Any]]) -> str:
        return write_jsonl(self.data_dir / self.s.project_id / name, rows)

    def batch(self, *artifacts: dict[str, Any], **extra: Any) -> Any:
        body = {
            "allocation_id": self.alloc["id"],
            "delivered_count": 300,
            "spend": "100",
            "artifacts": list(artifacts),
            "reported_metrics": {"agreement": 0.9},
            **extra,
        }
        return post_ok(self.client, "/v1/batches", self.admin, body)

    def checked(self, batch: Any) -> tuple[Any, Any]:
        """Let the worker run the checks; return (batch, latest quality run)."""
        run_once(self.db)
        got = self.client.get(f"/v1/batches/{batch['id']}", headers=self.admin).json()
        run = self.client.get(
            f"/v1/quality-runs/{got['quality']['run_id']}", headers=self.admin
        ).json()
        return got, run


def outcome(run: Any, name: str) -> str:
    return next(c["outcome"] for c in run["checks"] if c["name"] == name)


def check(run: Any, name: str) -> Any:
    return next(c for c in run["checks"] if c["name"] == name)


@pytest.fixture
def c(client: TestClient, admin: Headers, data_dir: Path, db: Session) -> Checked:
    return Checked(client, admin, data_dir, db)


def test_good_batch_passes(c: Checked) -> None:
    uri = c.file("good.jsonl", records(300))
    batch = c.batch({"uri": uri, "format": "jsonl", "record_count": 300})
    assert batch["status"] == "checking"

    got, run = c.checked(batch)
    assert (got["status"], run["status"]) == ("passed", "passed")
    assert {ch["name"]: ch["outcome"] for ch in run["checks"]} == {
        "files": "passed",
        "format": "passed",
        "schema": "passed",
        "duplicates": "passed",
        "stats": "passed",
        "attribute_counts": "passed",
        "acceptance_rules": "passed",
    }
    assert run["metrics"]["record_count"] == 300
    assert run["metrics"]["schema_valid_rate"] == 1.0
    assert run["attribute_counts"]["package_type"] == {
        "box": 100,
        "mailer": 100,
        "shrink_wrapped": 100,
    }
    assert got["quality"]["failed_checks"] == []
    rules = check(run, "acceptance_rules")["details"]["rules"]
    assert {r["key"]: (r["source"], r["value"]) for r in rules}["agreement"] == ("reported", 0.9)


def test_checksum_mismatch_fails_and_override_needs_a_reason(c: Checked) -> None:
    uri = c.file("tampered.jsonl", records(300))
    batch = c.batch({"uri": uri, "format": "jsonl", "sha256": "0" * 64})
    got, run = c.checked(batch)
    assert (got["status"], outcome(run, "files")) == ("failed", "failed")
    assert "checksum" in str(check(run, "files")["details"])
    assert got["quality"]["failed_checks"] == ["files"]

    path = f"/v1/batches/{batch['id']}/accept"
    refused = c.client.post(path, headers=c.admin, json={"accepted_count": 300})
    assert refused.status_code == 409
    assert "override_reason" in refused.json()["detail"]
    ok = c.client.post(
        path, headers=c.admin, json={"accepted_count": 300, "override_reason": "Re-uploaded; known"}
    ).json()
    assert (ok["status"], ok["override_reason"]) == ("accepted", "Re-uploaded; known")


def test_correct_checksum_and_size_pass(c: Checked) -> None:
    rows = records(30)
    uri = c.file("exact.jsonl", rows)
    data = Path(uri.removeprefix("file://")).read_bytes()
    batch = c.batch(
        {
            "uri": uri,
            "format": "jsonl",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        }
    )
    _, run = c.checked(batch)
    assert outcome(run, "files") == "passed"


def test_missing_and_outside_files_fail(c: Checked) -> None:
    missing = c.batch({"uri": (c.data_dir / "nope.jsonl").as_uri(), "format": "jsonl"})
    got, run = c.checked(missing)
    assert got["status"] == "failed"
    assert "File not found" in str(check(run, "files")["details"])

    outside = c.batch({"uri": "file:///etc/hosts", "format": "jsonl"})
    _, run = c.checked(outside)
    assert "must be inside" in str(check(run, "files")["details"])


def test_bad_lines_and_schema_failures(c: Checked) -> None:
    rows = records(90) + [{"id": "bad", "package_type": "crate", "severity": 9}] * 10
    path = c.data_dir / c.s.project_id / "messy.jsonl"
    uri = c.file("messy.jsonl", rows)
    with path.open("a") as f:
        f.write("this is not json\n[1, 2]\n")
    batch = c.batch({"uri": uri, "format": "jsonl", "record_count": 100})
    got, run = c.checked(batch)

    assert outcome(run, "format") == "warning"
    assert len(check(run, "format")["details"]["examples"]) == 2
    assert outcome(run, "schema") == "warning"
    assert run["metrics"]["schema_valid_rate"] == 0.9  # below the 0.95 rule
    assert outcome(run, "acceptance_rules") == "failed"
    assert "schema_valid_rate = 0.9" in check(run, "acceptance_rules")["summary"]
    assert got["status"] == "failed"
    assert outcome(run, "attribute_counts") == "warning"  # "crate" isn't in the spec


def test_duplicates_within_batch_and_against_accepted_batches(c: Checked) -> None:
    first = c.batch({"uri": c.file("a.jsonl", records(100)), "format": "jsonl"})
    c.checked(first)
    c.client.post(
        f"/v1/batches/{first['id']}/accept", headers=c.admin, json={"accepted_count": 100}
    )

    repeat = records(100)[:20] + records(80, prefix="new") + records(80, prefix="new")[:5]
    second = c.batch({"uri": c.file("b.jsonl", repeat), "format": "jsonl"})
    _, run = c.checked(second)
    assert run["metrics"]["duplicates_in_batch"] == 5
    assert run["metrics"]["duplicates_in_project"] == 20
    assert run["metrics"]["duplicate_rate"] == round(25 / 105, 4)
    assert outcome(run, "duplicates") == "warning"
    assert outcome(run, "acceptance_rules") == "failed"  # 0.238 > 0.05


def test_unaccepted_batches_are_not_duplicates(c: Checked) -> None:
    first = c.batch({"uri": c.file("a.jsonl", records(50)), "format": "jsonl"})
    c.checked(first)  # passed but never accepted
    second = c.batch({"uri": c.file("b.jsonl", records(50)), "format": "jsonl"})
    _, run = c.checked(second)
    assert run["metrics"]["duplicates_in_project"] == 0


def test_csv_files(c: Checked) -> None:
    path = c.data_dir / c.s.project_id / "rows.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("id,package_type\nc1,box\nc2,mailer\nc3,shrink_wrapped\n")
    # CSV values are text, so the schema's integer field isn't present; required fields are.
    _, run = c.checked(c.batch({"uri": path.as_uri(), "format": "csv"}))
    assert run["metrics"]["record_count"] == 3
    assert outcome(run, "format") == "passed"
    assert outcome(run, "schema") == "passed"


def test_parquet_is_not_supported_yet(c: Checked) -> None:
    path = c.data_dir / c.s.project_id / "x.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PAR1....PAR1")
    _, run = c.checked(c.batch({"uri": path.as_uri(), "format": "parquet"}))
    assert outcome(run, "files") == "passed"
    assert outcome(run, "format") == "warning"
    assert "not supported yet" in str(check(run, "format")["details"])


def test_rules_without_a_value_are_not_evaluated(c: Checked) -> None:
    batch = c.batch({"uri": c.file("a.jsonl", records(30)), "format": "jsonl"}, reported_metrics={})
    got, run = c.checked(batch)
    assert outcome(run, "acceptance_rules") == "warning"
    assert "no value for agreement" in check(run, "acceptance_rules")["summary"]
    assert got["status"] == "passed"


def test_s3_files(c: Checked, monkeypatch: pytest.MonkeyPatch) -> None:
    data = b"".join(f'{{"id": "s{i}", "package_type": "box"}}\n'.encode() for i in range(40))
    client = boto3.client(
        "s3", region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="y"
    )
    stubber = Stubber(client)
    stubber.add_response(
        "get_object",
        {"Body": StreamingBody(io.BytesIO(data), len(data))},
        {"Bucket": "intake", "Key": "surge/b1.jsonl"},
    )
    stubber.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
    stubber.activate()
    monkeypatch.setattr(storage, "s3_client_factory", lambda: client)

    batch = c.batch(
        {"uri": "s3://intake/surge/b1.jsonl", "format": "jsonl"},
        {"uri": "s3://intake/surge/missing.jsonl", "format": "jsonl"},
    )
    _, run = c.checked(batch)
    files = check(run, "files")["details"]["files"]
    assert files[0]["ok"] and files[0]["records"] == 40
    assert files[0]["sha256"] == hashlib.sha256(data).hexdigest()
    assert files[1]["problems"] == ["Not found: s3://intake/surge/missing.jsonl"]


def test_externally_decided_batches_keep_their_decision(c: Checked) -> None:
    rows = records(30) + records(30)[:10]  # duplicates: a finding, not a verdict
    batch = c.batch(
        {"uri": c.file("vendor.jsonl", rows), "format": "jsonl"},
        external_ref="vendor-7",
        decision={"status": "accepted", "decided_by": "surge-qa", "accepted_count": 40},
    )
    got, run = c.checked(batch)
    assert got["status"] == "accepted"
    assert run["status"] == "failed"  # duplicate_rate 0.25 > 0.05
    assert got["quality"]["failed_checks"] == ["acceptance_rules"]


def test_no_changes_or_decisions_while_checking(c: Checked) -> None:
    batch = c.batch({"uri": c.file("a.jsonl", records(30)), "format": "jsonl"})
    path = f"/v1/batches/{batch['id']}"
    assert (
        c.client.post(f"{path}/accept", headers=c.admin, json={"accepted_count": 1}).status_code
        == 409
    )
    assert c.client.post(f"{path}/reject", headers=c.admin, json={"reason": "x"}).status_code == 409
    assert c.client.patch(path, headers=c.admin, json={"notes": "x"}).status_code == 409
    assert c.client.delete(path, headers=c.admin).status_code == 409
    assert c.client.post(f"{path}/checks", headers=c.admin).status_code == 409


def test_rerun_after_fixing_a_file(c: Checked) -> None:
    uri = c.file("fixme.jsonl", [{"id": "x", "package_type": "crate"}] * 30)
    batch = c.batch({"uri": uri, "format": "jsonl"})
    got, _ = c.checked(batch)
    assert got["status"] == "failed"

    c.file("fixme.jsonl", records(30))
    again = c.client.post(f"/v1/batches/{batch['id']}/checks", headers=c.admin)
    assert (again.status_code, again.json()["trigger"]) == (202, "manual")
    got, run = c.checked(batch)
    assert (got["status"], run["status"]) == ("passed", "passed")
    runs = c.client.get(f"/v1/batches/{batch['id']}/quality-runs", headers=c.admin).json()["data"]
    assert [r["status"] for r in runs] == ["failed", "passed"]


def test_batches_without_files_skip_checks(c: Checked) -> None:
    batch = c.batch()
    assert (batch["status"], batch["quality"]) == ("received", None)
    assert c.client.post(f"/v1/batches/{batch['id']}/checks", headers=c.admin).status_code == 409


def test_coverage_uses_counts_from_files(c: Checked) -> None:
    rows = [{"id": f"x{i}", "package_type": "box" if i < 200 else "mailer"} for i in range(300)]
    batch = c.batch(
        {"uri": c.file("skewed.jsonl", rows), "format": "jsonl"},
    )
    c.checked(batch)
    report = c.client.get(f"/v1/batches/{batch['id']}/coverage", headers=c.admin).json()
    assert report["counts_from"] == {batch["id"]: "files"}
    [attr] = [a for a in report["attributes"] if a["attribute"] == "package_type"]
    shares = {v["value"]: v["actual_share"] for v in attr["values"]}
    assert shares["box"] == 0.6667
    assert any("shrink_wrapped" in g for g in report["gaps"])


def test_events_for_each_run(c: Checked) -> None:
    batch = c.batch({"uri": c.file("a.jsonl", records(30)), "format": "jsonl"})
    c.checked(batch)
    types = c.db.scalars(
        select(Event.type).where(Event.project_id == c.s.project_id).order_by(Event.id)
    ).all()
    assert types[-2:] == ["quality.completed", "batch.checked"]


def test_invalid_record_schema_is_refused(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    response = client.post(
        f"/v1/specs/{s.spec_id}/versions",
        headers=admin,
        json={"record_schema": {"type": "nonsense"}},
    )
    assert response.status_code == 422
    assert "record_schema isn't a valid JSON Schema" in response.json()["detail"]
