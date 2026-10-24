"""Portfolio maths, beyond the north-star numbers checked in tests/e2e/test_m5_flow.py."""

from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import MakeKey
from tests.helpers import Headers, Setup, post_ok


def scored(s: Setup, values: tuple[float, float], spend: tuple[str, str] = ("1000", "2000")) -> Any:
    """Two dataset versions (v2 baseline v1), one batch each, with main-metric results."""
    alloc = s.active_allocation()
    batches = []
    for amount in spend:
        b = s.batch(alloc["id"], spend=amount)
        batches.append(
            post_ok(s.client, f"/v1/batches/{b['id']}/accept", s.admin, {"accepted_count": 1000})
        )
    ds = post_ok(s.client, "/v1/datasets", s.admin, {"capability_id": s.capability_id, "name": "d"})
    versions = []
    for batch, value in zip(batches, values, strict=True):
        v = post_ok(
            s.client, f"/v1/datasets/{ds['id']}/versions", s.admin, {"batch_ids": [batch["id"]]}
        )
        post_ok(
            s.client, "/v1/eval-results", s.admin, {"dataset_version_id": v["id"], "value": value}
        )
        versions.append(v)
    return versions


def capability_row(client: TestClient, admin: Headers, query: str = "") -> Any:
    report = client.get(f"/v1/reports/portfolio{query}", headers=admin).json()
    [row] = report["by_capability"]
    return row


def test_lower_is_better_flips_the_sign(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    client.patch(
        f"/v1/capabilities/{s.capability_id}",
        headers=admin,
        json={"higher_is_better": False, "eval_metric": "error rate %"},
    )
    scored(s, (4.8, 4.1))  # error rate went down: an improvement
    row = capability_row(client, admin)
    assert row["eval_change_points"] == 0.7
    assert row["points_per_10k"] == 3.5  # 0.7 points for the 2,000 the new version added
    assert row["value"] == "17500.00"  # 0.7 × 25,000
    assert row["roi"] == 8.75


def test_point_size_scales_points(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    client.patch(f"/v1/capabilities/{s.capability_id}", headers=admin, json={"point_size": 0.01})
    scored(s, (0.80, 0.83))
    assert capability_row(client, admin)["eval_change_points"] == 3.0


def test_nothing_to_compare_is_explained(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    b = s.batch(alloc["id"], spend="1500")
    client.post(f"/v1/batches/{b['id']}/accept", headers=admin, json={"accepted_count": 1000})
    row = capability_row(client, admin)
    assert row["spend"] == [{"currency": "USD", "amount": "1500.00"}]
    assert row["usable_units"] == [{"unit": "images", "count": 1000}]
    assert row["cost_per_usable_unit"] == [{"unit": "images", "currency": "USD", "amount": "1.50"}]
    assert (row["eval_change_points"], row["points_per_10k"], row["value"], row["roi"]) == (
        None,
        None,
        None,
        None,
    )
    assert "No dataset version" in row["notes"][0]


def test_rejected_spend_raises_cost_per_usable_unit(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    good = s.batch(alloc["id"], spend="1000")
    client.post(f"/v1/batches/{good['id']}/accept", headers=admin, json={"accepted_count": 1000})
    bad = s.batch(alloc["id"], spend="500")
    client.post(f"/v1/batches/{bad['id']}/reject", headers=admin, json={"reason": "Off spec"})
    row = capability_row(client, admin)
    assert row["cost_per_usable_unit"][0]["amount"] == "1.50"  # 1,500 spend / 1,000 usable


def test_time_window(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    scored(s, (0.5, 0.6))
    future = capability_row(client, admin, "?since=2999-01-01T00:00:00Z")
    assert (future["spend"], future["eval_change_points"]) == ([], None)
    assert capability_row(client, admin, "?until=2999-01-01T00:00:00Z")["eval_change_points"] == 0.1


def test_every_number_has_a_source(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    v1, v2 = scored(s, (0.5, 0.6))
    row = capability_row(client, admin)
    assert row["sources"]["dataset_version_ids"] == [v2["id"]]
    assert len(row["sources"]["eval_result_ids"]) == 2
    assert row["sources"]["batch_count"] == 2


def test_project_keys_see_only_their_project(
    client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    mine = Setup(client, admin, "Mine")
    Setup(client, admin, "Theirs")
    key = make_key(role="project", project_id=mine.project_id, access="read")
    report = client.get("/v1/reports/portfolio", headers=key).json()
    assert [r["capability_id"] for r in report["by_capability"]] == [mine.capability_id]
    assert len(client.get("/v1/reports/portfolio", headers=admin).json()["by_capability"]) == 2
