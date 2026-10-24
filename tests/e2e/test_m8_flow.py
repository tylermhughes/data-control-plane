"""M8 end to end: diminishing returns plus a coverage gap -> 'refine the spec', drafted in one
click; and a plan for the next request that leans on the cheaper vendor."""

from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup, post_ok

SKEWED = {"package_type": {"box": 600, "mailer": 300, "shrink_wrapped": 100}}


def test_m8_diagnosis_to_draft_spec_and_next_plan(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    ds = post_ok(
        client, "/v1/datasets", admin, {"capability_id": s.capability_id, "name": "damage"}
    )
    for source, spend, value in (
        ("Surge", "1000", 0.50),
        ("Mercor", "800", 0.60),
        ("Surge", "1000", 0.61),
    ):
        alloc = s.active_allocation(source)
        batch = s.batch(alloc["id"], delivered_count=1000, spend=spend)
        post_ok(
            client,
            f"/v1/batches/{batch['id']}/accept",
            admin,
            {"accepted_count": 1000, "attribute_counts": SKEWED},
        )
        s.act("allocations", alloc["id"], "complete")
        v = post_ok(
            client, f"/v1/datasets/{ds['id']}/versions", admin, {"batch_ids": [batch["id"]]}
        )
        post_ok(client, "/v1/eval-results", admin, {"dataset_version_id": v["id"], "value": value})

    # 1. Returns flattened, and the data is short of shrink-wrapped: refine the spec.
    diagnosis = client.get(f"/v1/capabilities/{s.capability_id}/diagnosis", headers=admin).json()
    assert (diagnosis["trend"], diagnosis["recommendation"]) == ("flattening", "refine_spec")

    # 2. One click drafts the new targets; a person approves them.
    draft = post_ok(client, f"/v1/capabilities/{s.capability_id}/diagnosis/draft-spec", admin, {})
    approved = post_ok(
        client,
        f"/v1/specs/{s.spec_id}/versions/{draft['version']}/approve",
        admin,
        {"approved_by": "Priya Nair"},
    )
    assert approved["coverage_targets"]["package_type"]["shrink_wrapped"] > 0.35

    # 3. The next request, on the refined spec, gets a plan favouring the cheaper vendor.
    req = s.request(quantity=5000, spec_version_id=approved["id"])
    plan = client.get(f"/v1/requests/{req['id']}/allocation-plan", headers=admin).json()
    usable = {x["name"]: x["expected_usable"] for x in plan["suggestions"]}
    assert usable["Mercor"] > usable["Surge"]  # 800 vs 2,000 spend for the same usable units
    assert usable["Returns photos"] == 500  # untested: a 10% pilot
