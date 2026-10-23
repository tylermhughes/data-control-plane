from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from tests.conftest import MakeKey
from tests.helpers import Headers, Setup, post_ok


def test_create_starts_as_draft_in_capabilitys_project(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.request(priority="P1", requested_by="Priya Nair", due_date="2026-12-15")
    assert req["id"].startswith("req_")
    assert req["status"] == "draft"
    assert req["project_id"] == s.project_id
    assert req["priority"] == "P1"
    assert (req["spec_id"], req["spec_version"]) == (s.spec_id, 1)
    assert req["allocated"] == []


def test_defaults_and_validation(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    minimal = post_ok(
        client,
        "/v1/requests",
        admin,
        {"capability_id": s.capability_id, "title": "T", "quantity": 1},
    )
    assert (minimal["priority"], minimal["unit"], minimal["spec_version_id"]) == (
        "P2",
        "items",
        None,
    )
    for bad in ({"priority": "high"}, {"quantity": 0}, {"capability_id": "cap_nope"}):
        body = {"capability_id": s.capability_id, "title": "T", "quantity": 1, **bad}
        assert client.post("/v1/requests", headers=admin, json=body).status_code == 422, bad


def test_spec_version_must_be_in_same_project(client: TestClient, admin: Headers) -> None:
    a = Setup(client, admin, "A")
    b = Setup(client, admin, "B")
    response = client.post(
        "/v1/requests",
        headers=admin,
        json={
            "capability_id": a.capability_id,
            "title": "T",
            "quantity": 1,
            "spec_version_id": b.v1,
        },
    )
    assert response.status_code == 422


def test_open_needs_an_approved_spec_version(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    no_spec = s.request(spec_version_id=None)
    response = s.act("requests", no_spec["id"], "open")
    assert response.status_code == 409
    assert "approved spec version" in response.json()["detail"]

    draft_v2 = post_ok(client, f"/v1/specs/{s.spec_id}/versions", admin, {})
    with_draft = s.request(spec_version_id=draft_v2["id"])
    assert s.act("requests", with_draft["id"], "open").status_code == 409

    opened = s.act("requests", s.request()["id"], "open").json()
    assert opened["status"] == "open"
    assert opened["opened_at"] is not None


def test_open_request_keeps_an_approved_spec(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    draft_v2 = post_ok(client, f"/v1/specs/{s.spec_id}/versions", admin, {})
    path = f"/v1/requests/{req['id']}"
    assert (
        client.patch(path, headers=admin, json={"spec_version_id": draft_v2["id"]}).status_code
        == 409
    )
    assert client.patch(path, headers=admin, json={"spec_version_id": None}).status_code == 409

    post_ok(client, f"/v1/specs/{s.spec_id}/versions/2/approve", admin, {"approved_by": "PM"})
    moved = client.patch(path, headers=admin, json={"spec_version_id": draft_v2["id"]}).json()
    assert moved["spec_version"] == 2


def test_lifecycle_and_frozen_after_close(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    assert s.act("requests", req["id"], "open").status_code == 409  # already open
    closed = s.act("requests", req["id"], "close").json()
    assert closed["status"] == "closed"
    assert (
        client.patch(f"/v1/requests/{req['id']}", headers=admin, json={"title": "x"}).status_code
        == 409
    )
    assert s.act("requests", req["id"], "cancel").status_code == 409


def test_close_refused_while_allocations_active(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    active = s.allocate(req["id"], "Surge")
    s.act("allocations", active["id"], "activate")
    planned = s.allocate(req["id"], "Mercor")

    response = s.act("requests", req["id"], "close")
    assert response.status_code == 409
    assert active["id"] in response.json()["detail"]

    s.act("allocations", active["id"], "complete")
    assert s.act("requests", req["id"], "close").json()["status"] == "closed"
    planned_now = client.get(f"/v1/allocations/{planned['id']}", headers=admin).json()
    assert planned_now["status"] == "cancelled"  # never started, so cancelled on close


def test_cancel_cascades_to_unfinished_allocations(
    client: TestClient, admin: Headers, db: Session
) -> None:
    s = Setup(client, admin)
    req = s.open_request()
    done = s.allocate(req["id"], "Surge")
    s.act("allocations", done["id"], "activate")
    s.act("allocations", done["id"], "complete")
    running = s.allocate(req["id"], "Mercor")
    s.act("allocations", running["id"], "activate")
    planned = s.allocate(req["id"], "Returns photos")

    assert s.act("requests", req["id"], "cancel").json()["status"] == "cancelled"
    statuses = {
        a["id"]: a["status"]
        for a in client.get(f"/v1/allocations?request_id={req['id']}", headers=admin).json()["data"]
    }
    assert statuses == {
        done["id"]: "complete",
        running["id"]: "cancelled",
        planned["id"]: "cancelled",
    }

    cancelled_events = db.scalars(
        select(Event.subject_id).where(Event.type == "allocation.cancelled")
    ).all()
    assert sorted(cancelled_events) == sorted([running["id"], planned["id"]])


def test_delete_only_without_allocations(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    empty = s.request()
    assert client.delete(f"/v1/requests/{empty['id']}", headers=admin).status_code == 204

    used = s.request()
    s.allocate(used["id"], "Surge")
    response = client.delete(f"/v1/requests/{used['id']}", headers=admin)
    assert response.status_code == 409
    assert "Cancel it instead" in response.json()["detail"]


def test_list_filters(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    s.request()
    opened = s.open_request()
    only_open = client.get("/v1/requests?status=open", headers=admin).json()["data"]
    assert [r["id"] for r in only_open] == [opened["id"]]
    by_cap = client.get(f"/v1/requests?capability_id={s.capability_id}", headers=admin).json()
    assert len(by_cap["data"]) == 2


def test_project_keys_stay_in_their_project(
    client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    mine = Setup(client, admin, "Mine")
    theirs = Setup(client, admin, "Theirs")
    key = make_key(role="project", project_id=mine.project_id)
    other = theirs.request()

    assert client.get(f"/v1/requests/{other['id']}", headers=key).status_code == 404
    assert client.get("/v1/requests", headers=key).json()["data"] == []
    sneaky = client.post(
        "/v1/requests",
        headers=key,
        json={"capability_id": theirs.capability_id, "title": "T", "quantity": 1},
    )
    assert sneaky.status_code == 422
    own = client.post(
        "/v1/requests",
        headers=key,
        json={"capability_id": mine.capability_id, "title": "T", "quantity": 1},
    )
    assert own.status_code == 201
