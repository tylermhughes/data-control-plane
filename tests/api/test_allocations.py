from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup, post_ok


def test_quoted_cost_and_request_totals(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    a = s.allocate(req["id"], "Surge", quantity=4000, quoted_unit_rate="1.55")
    assert a["id"].startswith("alc_")
    assert a["status"] == "planned"
    assert a["quoted_cost"] == "6200.00"
    assert a["unit"] == "images"  # the source's default unit
    assert a["spec_version_id"] == s.v1

    s.allocate(req["id"], "Mercor", quantity=4000, quoted_unit_rate="1.6525")
    s.allocate(req["id"], "Returns photos", quantity=3000, quoted_unit_rate="0.1833")
    s.allocate(req["id"], "Picking sim", quantity=300, quoted_unit_rate="80")
    cancelled = s.allocate(req["id"], "Surge", quantity=999, quoted_unit_rate="9")
    s.act("allocations", cancelled["id"], "cancel")

    totals = client.get(f"/v1/requests/{req['id']}", headers=admin).json()["allocated"]
    assert totals == [
        # 6200 + 6610 + 549.90 = 13359.90; the cancelled allocation is excluded.
        {"unit": "images", "currency": "USD", "quantity": 11000, "quoted_cost": "13359.90"},
        {"unit": "tasks", "currency": "USD", "quantity": 300, "quoted_cost": "24000.00"},
    ]


def test_over_allocation_is_allowed(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request(quantity=1000)
    s.allocate(req["id"], "Surge", quantity=1500)
    total = client.get(f"/v1/requests/{req['id']}", headers=admin).json()["allocated"][0]
    assert total["quantity"] == 1500


def test_needs_approved_spec_and_live_request(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    no_spec = s.request(spec_version_id=None)
    response = client.post(
        "/v1/allocations",
        headers=admin,
        json={
            "request_id": no_spec["id"],
            "data_source_id": s.sources["Surge"],
            "quantity": 1,
            "quoted_unit_rate": "1",
            "currency": "USD",
        },
    )
    assert response.status_code == 409
    assert "approved spec version" in response.json()["detail"]

    draft = s.request()  # draft requests with an approved spec can be planned
    assert s.allocate(draft["id"], "Surge")["status"] == "planned"

    closed = s.open_request()
    s.act("requests", closed["id"], "close")
    response = client.post(
        "/v1/allocations",
        headers=admin,
        json={
            "request_id": closed["id"],
            "data_source_id": s.sources["Surge"],
            "quantity": 1,
            "quoted_unit_rate": "1",
            "currency": "USD",
        },
    )
    assert response.status_code == 409


def test_source_must_be_in_same_project(client: TestClient, admin: Headers) -> None:
    a = Setup(client, admin, "A")
    b = Setup(client, admin, "B")
    req = a.open_request()
    response = client.post(
        "/v1/allocations",
        headers=admin,
        json={
            "request_id": req["id"],
            "data_source_id": b.sources["Surge"],
            "quantity": 1,
            "quoted_unit_rate": "1",
            "currency": "USD",
        },
    )
    assert response.status_code == 422


def test_pins_spec_version_even_after_request_moves_on(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    first = s.allocate(req["id"], "Surge")
    v2 = post_ok(client, f"/v1/specs/{s.spec_id}/versions", admin, {})
    post_ok(client, f"/v1/specs/{s.spec_id}/versions/2/approve", admin, {"approved_by": "PM"})
    client.patch(f"/v1/requests/{req['id']}", headers=admin, json={"spec_version_id": v2["id"]})
    second = s.allocate(req["id"], "Mercor")

    assert (
        client.get(f"/v1/allocations/{first['id']}", headers=admin).json()["spec_version_id"]
        == s.v1
    )
    assert second["spec_version_id"] == v2["id"]


def test_activate_needs_open_request(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    draft = s.request()
    alloc = s.allocate(draft["id"], "Surge")
    response = s.act("allocations", alloc["id"], "activate")
    assert response.status_code == 409
    assert "Open the request first" in response.json()["detail"]

    s.act("requests", draft["id"], "open")
    assert s.act("allocations", alloc["id"], "activate").json()["status"] == "active"


def test_lifecycle_transitions(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    alloc = s.allocate(req["id"], "Surge")
    assert s.act("allocations", alloc["id"], "complete").status_code == 409  # not active yet
    active = s.act("allocations", alloc["id"], "activate").json()
    assert active["activated_at"] is not None
    done = s.act("allocations", alloc["id"], "complete").json()
    assert (done["status"], done["completed_at"] is not None) == ("complete", True)
    assert s.act("allocations", alloc["id"], "cancel").status_code == 409


def test_what_can_change_by_status(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    alloc = s.allocate(req["id"], "Surge")
    path = f"/v1/allocations/{alloc['id']}"

    planned = client.patch(path, headers=admin, json={"quoted_unit_rate": "1.40", "quantity": 5000})
    assert planned.json()["quoted_cost"] == "7000.00"

    s.act("allocations", alloc["id"], "activate")
    ok = client.patch(
        path, headers=admin, json={"quantity": 6000, "due_date": "2026-12-20", "notes": "+1k"}
    )
    assert ok.status_code == 200
    frozen = client.patch(path, headers=admin, json={"quoted_unit_rate": "1.00"})
    assert frozen.status_code == 409
    assert "quoted_unit_rate can't change" in frozen.json()["detail"]

    s.act("allocations", alloc["id"], "complete")
    assert client.patch(path, headers=admin, json={"notes": "x"}).status_code == 409


def test_delete_only_planned(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    planned = s.allocate(req["id"], "Surge")
    assert client.delete(f"/v1/allocations/{planned['id']}", headers=admin).status_code == 204
    active = s.allocate(req["id"], "Surge")
    s.act("allocations", active["id"], "activate")
    assert client.delete(f"/v1/allocations/{active['id']}", headers=admin).status_code == 409
