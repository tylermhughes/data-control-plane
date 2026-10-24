from typing import Any

from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup, post_ok

# SPEC_CONTENT targets: package_type box 0.30 / mailer 0.35 / shrink_wrapped 0.35; zone induct 0.6.


def accept(s: Setup, batch: Any, accepted: int, counts: dict[str, dict[str, int]]) -> Any:
    return post_ok(
        s.client,
        f"/v1/batches/{batch['id']}/accept",
        s.admin,
        {"accepted_count": accepted, "attribute_counts": counts},
    )


def by_value(report: Any, attribute: str) -> dict[str, Any]:
    [attr] = [a for a in report["attributes"] if a["attribute"] == attribute]
    return {v["value"]: v for v in attr["values"]}


def test_batch_coverage_flags_values_below_target(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"], delivered_count=1000)
    accept(s, batch, 1000, {"package_type": {"box": 380, "mailer": 340, "shrink_wrapped": 280}})

    report = client.get(f"/v1/batches/{batch['id']}/coverage", headers=admin).json()
    assert report["tolerance"] == 0.05
    assert report["accepted_count"] == 1000
    values = by_value(report, "package_type")
    assert values["shrink_wrapped"] == {
        "value": "shrink_wrapped",
        "count": 280,
        "actual_share": 0.28,
        "target_share": 0.35,
        "gap": -0.07,
        "status": "below",  # 7 points under, tolerance 5
    }
    assert values["mailer"]["status"] == "ok"  # 1 point under: within tolerance
    assert values["box"]["status"] == "ok"  # above target is fine
    assert report["gaps"] == ["package_type=shrink_wrapped: 28% vs 35% target"]
    zone = by_value(report, "zone")
    assert zone["induct"]["status"] == "no_data"
    assert zone["sort"]["status"] == "no_target"


def test_tolerance_comes_from_the_spec_version(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    strict = post_ok(client, f"/v1/specs/{s.spec_id}/versions", admin, {"coverage_tolerance": 0})
    assert strict["coverage_tolerance"] == 0
    post_ok(client, f"/v1/specs/{s.spec_id}/versions/2/approve", admin, {"approved_by": "PM"})
    req = s.open_request(spec_version_id=strict["id"])
    alloc = s.allocate(req["id"], "Surge")
    s.act("allocations", alloc["id"], "activate")
    batch = s.batch(alloc["id"])
    accept(s, batch, 1000, {"package_type": {"box": 310, "mailer": 340, "shrink_wrapped": 350}})
    report = client.get(f"/v1/batches/{batch['id']}/coverage", headers=admin).json()
    assert by_value(report, "package_type")["mailer"]["status"] == "below"


def test_request_coverage_adds_up_accepted_batches(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    first = s.batch(alloc["id"])
    accept(s, first, 1000, {"package_type": {"box": 500, "mailer": 400, "shrink_wrapped": 100}})
    second = s.batch(alloc["id"])
    accept(s, second, 1000, {"package_type": {"box": 100, "mailer": 300, "shrink_wrapped": 600}})
    rejected = s.batch(alloc["id"])
    client.post(f"/v1/batches/{rejected['id']}/reject", headers=admin, json={"reason": "x"})

    report = client.get(f"/v1/requests/{alloc['request_id']}/coverage", headers=admin).json()
    assert report["accepted_count"] == 2000
    assert sorted(report["batch_ids"]) == sorted([first["id"], second["id"]])
    values = by_value(report, "package_type")
    assert (values["box"]["count"], values["shrink_wrapped"]["actual_share"]) == (600, 0.35)
    assert report["gaps"] == []


def test_counts_cover_only_part_of_the_data(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"])
    accept(s, batch, 1000, {"package_type": {"box": 100, "mailer": 100, "shrink_wrapped": 50}})
    report = client.get(f"/v1/batches/{batch['id']}/coverage", headers=admin).json()
    [attr] = [a for a in report["attributes"] if a["attribute"] == "package_type"]
    assert (attr["counted"], attr["counted_share_of_accepted"]) == (250, 0.25)


def test_request_without_spec_has_no_coverage(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.request(spec_version_id=None)
    assert client.get(f"/v1/requests/{req['id']}/coverage", headers=admin).status_code == 409
