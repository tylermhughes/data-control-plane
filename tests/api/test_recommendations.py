"""Recommendations v0: allocation plans and the diagnosis."""

from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from app.models.base import utcnow
from tests.helpers import Headers, Setup, post_ok


def delivered(
    s: Setup,
    source: str,
    *,
    delivered: int,
    accepted: int,
    spend: str,
    counts: dict[str, dict[str, int]] | None = None,
    request_id: str | None = None,
    complete: bool = True,
) -> Any:
    """Give a source some history: one allocation with one accepted batch."""
    if request_id is None:
        alloc = s.active_allocation(source)
    else:
        alloc = s.act("allocations", s.allocate(request_id, source)["id"], "activate").json()
    batch = s.batch(alloc["id"], delivered_count=delivered, spend=spend)
    body: dict[str, Any] = {"accepted_count": accepted}
    if counts:
        body["attribute_counts"] = counts
    post_ok(s.client, f"/v1/batches/{batch['id']}/accept", s.admin, body)
    if complete:
        s.act("allocations", alloc["id"], "complete")
    return alloc


def plan(s: Setup, request_id: str) -> Any:
    response = s.client.get(f"/v1/requests/{request_id}/allocation-plan", headers=s.admin)
    assert response.status_code == 200, response.text
    return response.json()


def by_name(p: Any) -> dict[str, Any]:
    return {x["name"]: x for x in p["suggestions"]}


def test_split_weighted_by_value_with_pilot_for_new_sources(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    delivered(s, "Surge", delivered=1000, accepted=900, spend="1500")  # 1.6667 per usable
    delivered(s, "Mercor", delivered=1000, accepted=800, spend="1000")  # 1.25 per usable
    req = s.request(quantity=10000)

    p = plan(s, req["id"])
    assert (p["requested"], p["already_allocated"], p["remaining"], p["shortfall"]) == (
        10000,
        0,
        10000,
        0,
    )
    got = by_name(p)
    assert set(got) == {"Surge", "Mercor", "Returns photos"}
    assert [e["name"] for e in p["excluded"]] == ["Picking sim"]  # delivers tasks, not images

    pilot = got["Returns photos"]
    assert (pilot["role"], pilot["expected_usable"], pilot["order_quantity"]) == (
        "pilot",
        1000,
        1000,
    )
    surge, mercor = got["Surge"], got["Mercor"]
    assert (surge["role"], mercor["role"]) == ("proven", "proven")
    # 9,000 shared in proportion to 1/1.6667 : 1/1.25 = 0.6 : 0.8
    assert (surge["expected_usable"], mercor["expected_usable"]) == (3857, 5143)
    assert surge["order_quantity"] == 4286  # 3857 / 0.9 accept rate
    assert mercor["order_quantity"] == 6429  # 5143 / 0.8
    assert surge["expected_cost"] == "6643.30"  # 4286 × 1.55 last quote
    assert surge["evidence"]["accept_rate"] == 0.9
    assert surge["evidence"]["cost_per_usable_unit"] == "1.6667"
    assert "extra to cover its 10% rejects" in surge["notes"][0]


def test_suggested_allocation_can_be_created_as_is(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    delivered(s, "Surge", delivered=100, accepted=100, spend="150")
    req = s.request(quantity=500, due_date=(utcnow() + timedelta(days=30)).date().isoformat())
    suggestion = by_name(plan(s, req["id"]))["Surge"]
    created = post_ok(client, "/v1/allocations", admin, suggestion["allocation"])
    assert (created["quantity"], created["quoted_unit_rate"]) == (
        suggestion["order_quantity"],
        "1.55",
    )
    assert plan(s, req["id"])["already_allocated"] == created["quantity"]


def test_capacity_caps_and_shortfall(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    delivered(s, "Surge", delivered=1000, accepted=900, spend="1500")
    delivered(s, "Mercor", delivered=1000, accepted=800, spend="1000")
    due = (utcnow() + timedelta(days=3)).date().isoformat()
    p = plan(s, s.request(quantity=10000, due_date=due)["id"])
    got = by_name(p)
    # First deliveries today, so throughput = accepted per day: 900 and 800; 3 days left.
    assert got["Surge"]["capacity_by_due_date"] == 2700
    assert got["Surge"]["expected_usable"] == 2700
    assert got["Mercor"]["expected_usable"] == 2400
    assert "Capped" in " ".join(got["Surge"]["notes"])
    assert p["shortfall"] == 10000 - 1000 - 2700 - 2400


def test_open_commitments_reduce_capacity(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    delivered(s, "Surge", delivered=1000, accepted=900, spend="1500", complete=False)  # owes 3,100
    due = (utcnow() + timedelta(days=3)).date().isoformat()
    p = plan(s, s.request(quantity=10000, due_date=due)["id"])
    assert "Surge" not in by_name(p)  # 2,700 capacity − 3,100 owed: nothing left
    assert p["shortfall"] > 0


def test_rights_expiring_before_due_date_exclude_a_source(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    delivered(s, "Surge", delivered=100, accepted=100, spend="150")
    soon = (utcnow() + timedelta(days=5)).date().isoformat()
    client.patch(
        f"/v1/data-sources/{s.sources['Surge']}", headers=admin, json={"rights_expires_at": soon}
    )
    due = (utcnow() + timedelta(days=20)).date().isoformat()
    p = plan(s, s.request(quantity=1000, due_date=due)["id"])
    [excluded] = [e for e in p["excluded"] if e["name"] == "Surge"]
    assert "before the due date" in excluded["reason"]


def test_fully_allocated_request_needs_nothing(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.request(quantity=1000)
    s.allocate(req["id"], "Surge", quantity=1000)
    p = plan(s, req["id"])
    assert (p["remaining"], p["suggestions"]) == (0, [])


def test_coverage_fit_is_shown_as_evidence(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request(quantity=10000)
    delivered(
        s,
        "Surge",
        delivered=1000,
        accepted=1000,
        spend="1000",
        request_id=req["id"],
        counts={"package_type": {"box": 700, "mailer": 250, "shrink_wrapped": 50}},
    )
    delivered(
        s,
        "Mercor",
        delivered=500,
        accepted=500,
        spend="600",
        request_id=req["id"],
        counts={"package_type": {"box": 100, "mailer": 100, "shrink_wrapped": 300}},
    )
    p = plan(s, req["id"])
    assert any("shrink_wrapped" in g for g in p["coverage_gaps"])
    mercor_notes = " ".join(by_name(p)["Mercor"]["notes"])
    assert (
        "Delivers 60% package_type=shrink_wrapped, which the request is short of." in mercor_notes
    )


# --- diagnosis -------------------------------------------------------------------------------


def versions(
    s: Setup, evals: list[float], counts: dict[str, dict[str, int]] | None = None
) -> list[Any]:
    """Dataset versions v1..vn, each adding one 1,000-spend batch, with main-metric results."""
    ds = post_ok(s.client, "/v1/datasets", s.admin, {"capability_id": s.capability_id, "name": "d"})
    out = []
    for value in evals:
        alloc = s.active_allocation()
        b = s.batch(alloc["id"], delivered_count=1000, spend="1000")
        body: dict[str, Any] = {"accepted_count": 1000}
        if counts:
            body["attribute_counts"] = counts
        post_ok(s.client, f"/v1/batches/{b['id']}/accept", s.admin, body)
        v = post_ok(
            s.client, f"/v1/datasets/{ds['id']}/versions", s.admin, {"batch_ids": [b["id"]]}
        )
        post_ok(
            s.client, "/v1/eval-results", s.admin, {"dataset_version_id": v["id"], "value": value}
        )
        out.append(v)
    return out


def diagnose(s: Setup) -> Any:
    response = s.client.get(f"/v1/capabilities/{s.capability_id}/diagnosis", headers=s.admin)
    assert response.status_code == 200, response.text
    return response.json()


SKEWED = {"package_type": {"box": 600, "mailer": 300, "shrink_wrapped": 100}}
BALANCED = {"package_type": {"box": 300, "mailer": 350, "shrink_wrapped": 350}}


def test_not_enough_data(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    versions(s, [0.5, 0.6])
    d = diagnose(s)
    assert (d["trend"], d["recommendation"], len(d["versions"])) == (
        "not_enough_data",
        "not_enough_data",
        1,
    )


def test_improving_means_keep_going(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    versions(s, [0.5, 0.6, 0.7])
    d = diagnose(s)
    assert [v["points_per_10k"] for v in d["versions"]] == [1.0, 1.0]
    assert (d["trend"], d["recommendation"], d["latest_vs_earlier"]) == (
        "improving",
        "keep_going",
        1.0,
    )


def test_flattening_with_a_data_mix_gap_means_refine_the_spec(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    versions(s, [0.5, 0.6, 0.61], counts=SKEWED)
    d = diagnose(s)
    assert (d["trend"], d["recommendation"]) == ("flattening", "refine_spec")
    assert d["latest_vs_earlier"] == 0.1
    assert d["checks"][0] == {
        "cause": "data_mix",
        "status": "found",
        "summary": "package_type=shrink_wrapped: 10% vs 35% target",
    }
    assert {c["cause"]: c["status"] for c in d["checks"][1:]} == {
        "label_quality": "not_checked",
        "eval": "not_checked",
        "model": "not_checked",
        "saturation": "not_checked",
    }
    assert "Refine the spec" in d["summary"]
    change = d["suggested_spec_change"]
    assert change["spec_id"] == s.spec_id
    assert change["coverage_targets"]["package_type"] == {
        "box": 0.24,
        "mailer": 0.28,
        "shrink_wrapped": 0.48,
    }
    assert change["coverage_targets"]["zone"] == {"induct": 0.6}


def test_one_click_draft_of_the_suggested_spec(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    versions(s, [0.5, 0.6, 0.61], counts=SKEWED)
    path = f"/v1/capabilities/{s.capability_id}/diagnosis/draft-spec"
    draft = client.post(path, headers=admin)
    assert draft.status_code == 201, draft.text
    body = draft.json()
    assert (body["status"], body["version"]) == ("draft", 2)
    assert body["coverage_targets"]["package_type"]["shrink_wrapped"] == 0.48
    assert body["change_note"].startswith("Drafted by Data Control Plane")
    again = client.post(path, headers=admin)
    assert again.status_code == 409  # the spec already has a draft


def test_flattening_without_a_gap_means_investigate_not_cut(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    versions(s, [0.5, 0.6, 0.61], counts=BALANCED)
    d = diagnose(s)
    assert (d["trend"], d["recommendation"]) == ("flattening", "investigate")
    assert d["checks"][0]["status"] == "ok"
    assert "before cutting spend" in d["summary"]
    assert d["suggested_spec_change"] is None
    draft = client.post(f"/v1/capabilities/{s.capability_id}/diagnosis/draft-spec", headers=admin)
    assert draft.status_code == 409


def test_threshold_is_per_capability(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    client.patch(
        f"/v1/capabilities/{s.capability_id}", headers=admin, json={"flattening_threshold": 0.05}
    )
    versions(s, [0.5, 0.6, 0.61], counts=SKEWED)
    d = diagnose(s)
    assert (d["flattening_threshold"], d["trend"], d["recommendation"]) == (
        0.05,
        "improving",
        "keep_going",
    )
