"""The bucket watcher, against a real S3-compatible server (Versity Gateway)."""

import json
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.services import connectors
from app.worker.__main__ import run_once
from tests import s3
from tests.helpers import Headers, Setup, post_ok


def jsonl(n: int, prefix: str = "r") -> bytes:
    types = ["box", "mailer", "shrink_wrapped"]
    zones = ["induct", "sort"]
    return "".join(
        json.dumps({"id": f"{prefix}{i}", "package_type": types[i % 3], "zone": zones[i % 2]})
        + "\n"
        for i in range(n)
    ).encode()


class Watched:
    def __init__(self, client: TestClient, admin: Headers, **extra: Any) -> None:
        self.client, self.admin = client, admin
        self.s = Setup(client, admin)
        self.alloc = self.s.active_allocation(quantity=4000, quoted_unit_rate="1.55")
        self.bucket = s3.new_bucket()
        body = {
            "data_source_id": self.s.sources["Surge"],
            "bucket": self.bucket,
            "prefix": "surge/",
            "endpoint_url": s3.ENDPOINT,
            "credentials": {"access_key_id": s3.ACCESS_KEY, "secret_access_key": s3.SECRET_KEY},
            **extra,
        }
        self.cnx = post_ok(client, "/v1/connectors", admin, body)

    def poll(self) -> Any:
        response = self.client.post(f"/v1/connectors/{self.cnx['id']}/poll", headers=self.admin)
        assert response.status_code == 200, response.text
        return response.json()

    def batch(self, batch_id: str) -> Any:
        return self.client.get(f"/v1/batches/{batch_id}", headers=self.admin).json()


@pytest.fixture
def w(client: TestClient, admin: Headers) -> Watched:
    return Watched(client, admin)


def test_new_files_become_checked_batches(w: Watched, db: Session) -> None:
    s3.put(w.bucket, "surge/delivery-1.jsonl", jsonl(300))
    result = w.poll()
    assert (result["files_listed"], len(result["new_batches"]), result["errors"]) == (1, 1, [])

    batch = w.batch(result["new_batches"][0])
    assert batch["status"] == "checking"
    assert batch["allocation_id"] == w.alloc["id"]
    assert batch["external_ref"] == "s3:surge/delivery-1.jsonl"
    assert batch["artifacts"][0]["uri"] == f"s3://{w.bucket}/surge/delivery-1.jsonl"
    assert (batch["delivered_count_from_files"], batch["spend_is_estimate"]) == (True, True)

    run_once(db)  # checks read the file with the connector's own credentials
    batch = w.batch(batch["id"])
    assert batch["status"] == "passed"
    assert batch["delivered_count"] == 300  # from the file
    assert batch["spend"] == "465.00"  # estimate: 300 × 1.55
    cov = w.client.get(f"/v1/batches/{batch['id']}/coverage", headers=w.admin).json()
    assert cov["counts_from"] == {batch["id"]: "files"}

    connector = w.client.get(f"/v1/connectors/{w.cnx['id']}", headers=w.admin).json()
    assert connector["last_found_at"] and connector["last_error"] is None


def test_files_are_picked_up_once(w: Watched) -> None:
    s3.put(w.bucket, "surge/a.jsonl", jsonl(10))
    assert len(w.poll()["new_batches"]) == 1
    again = w.poll()
    assert (again["files_listed"], again["new_batches"]) == (1, [])
    s3.put(w.bucket, "surge/b.jsonl", jsonl(10, "b"))
    assert len(w.poll()["new_batches"]) == 1
    objects = w.client.get(f"/v1/connectors/{w.cnx['id']}/objects", headers=w.admin).json()
    assert [o["key"] for o in objects["data"]] == ["surge/a.jsonl", "surge/b.jsonl"]


def test_only_data_files_under_the_prefix(w: Watched) -> None:
    for key in (
        "surge/ok.jsonl",
        "surge/ok.csv",
        "surge/_manifest.jsonl",
        "surge/.hidden.jsonl",
        "surge/readme.txt",
        "other/elsewhere.jsonl",
    ):
        s3.put(w.bucket, key, jsonl(3))
    result = w.poll()
    keys = sorted(w.batch(b)["external_ref"] for b in result["new_batches"])
    assert keys == ["s3:surge/ok.csv", "s3:surge/ok.jsonl"]


def test_changed_file_is_checked_again(w: Watched, db: Session) -> None:
    s3.put(w.bucket, "surge/fix.jsonl", b'{"id": "x", "package_type": "crate"}\n' * 5)
    [batch_id] = w.poll()["new_batches"]
    run_once(db)
    runs_before = len(
        w.client.get(f"/v1/batches/{batch_id}/quality-runs", headers=w.admin).json()["data"]
    )

    s3.put(w.bucket, "surge/fix.jsonl", jsonl(20))
    result = w.poll()
    assert (result["new_batches"], result["updated_files"]) == ([], ["surge/fix.jsonl"])
    run_once(db)
    runs = w.client.get(f"/v1/batches/{batch_id}/quality-runs", headers=w.admin).json()["data"]
    assert len(runs) == runs_before + 1
    assert w.batch(batch_id)["delivered_count"] == 20


def test_errors_are_recorded_and_retried(client: TestClient, admin: Headers) -> None:
    w = Watched(
        client,
        admin,
        credentials={"access_key_id": s3.ACCESS_KEY, "secret_access_key": "wrong"},
    )
    s3.put(w.bucket, "surge/a.jsonl", jsonl(3))
    result = w.poll()
    assert result["new_batches"] == []
    assert "Access denied" in result["errors"][0]
    got = client.get(f"/v1/connectors/{w.cnx['id']}", headers=admin).json()
    assert "Check the connector's credentials" in got["last_error"]

    client.patch(
        f"/v1/connectors/{w.cnx['id']}",
        headers=admin,
        json={"credentials": {"access_key_id": s3.ACCESS_KEY, "secret_access_key": s3.SECRET_KEY}},
    )
    assert len(w.poll()["new_batches"]) == 1
    assert client.get(f"/v1/connectors/{w.cnx['id']}", headers=admin).json()["last_error"] is None


def test_file_waits_until_there_is_an_active_allocation(w: Watched) -> None:
    w.s.act("allocations", w.alloc["id"], "complete")
    s3.put(w.bucket, "surge/early.jsonl", jsonl(3))
    result = w.poll()
    assert result["new_batches"] == []
    assert "no active allocation" in result["errors"][0]

    w.s.active_allocation()
    assert len(w.poll()["new_batches"]) == 1  # tried again on the next poll


def test_credentials_are_encrypted_and_never_shown(w: Watched, db: Session) -> None:
    got = w.client.get(f"/v1/connectors/{w.cnx['id']}", headers=w.admin).json()
    assert (got["has_credentials"], got["access_key_hint"]) == (True, "…cess")
    assert "credentials" not in got and s3.SECRET_KEY not in json.dumps(got)
    stored = db.execute(
        text("SELECT credentials_encrypted FROM connectors WHERE id = :id"), {"id": w.cnx["id"]}
    ).scalar_one()
    assert s3.SECRET_KEY not in stored and s3.ACCESS_KEY not in stored

    cleared = w.client.patch(
        f"/v1/connectors/{w.cnx['id']}", headers=w.admin, json={"credentials": None}
    ).json()
    assert (cleared["has_credentials"], cleared["access_key_hint"]) == (False, None)


def test_worker_polls_on_schedule(w: Watched, db: Session) -> None:
    s3.put(w.bucket, "surge/scheduled.jsonl", jsonl(3))
    assert connectors.poll_due(db) == 1  # new connectors are due right away
    assert connectors.poll_due(db) == 0  # not again until poll_interval_seconds have passed
    later = utcnow() + timedelta(seconds=61)
    assert connectors.poll_due(db, now=later) == 1
    batches = w.client.get("/v1/batches", headers=w.admin).json()["data"]
    assert len(batches) == 1


def test_disabled_connectors_are_not_polled(w: Watched, db: Session) -> None:
    w.client.patch(f"/v1/connectors/{w.cnx['id']}", headers=w.admin, json={"enabled": False})
    assert connectors.poll_due(db) == 0
    response = w.client.post(f"/v1/connectors/{w.cnx['id']}/poll", headers=w.admin)
    assert response.status_code == 409


def test_validation(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    base = {"data_source_id": s.sources["Surge"], "bucket": "intake"}
    for bad in (
        {"endpoint_url": "ftp://x"},
        {"endpoint_url": "http://169.254.169.254/"},
        {"poll_interval_seconds": 5},
        {"bucket": "a"},
        {"allocation_id": "alc_nope"},
    ):
        assert (
            client.post("/v1/connectors", headers=admin, json={**base, **bad}).status_code == 422
        ), bad
