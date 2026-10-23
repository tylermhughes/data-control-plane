from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from tests.helpers import Headers, new_project, post_ok

BODY = {
    "name": "Package damage detection",
    "eval_metric": "recall@0.5",
    "value_per_point": "25000.00",
    "currency": "USD",
}


def test_create_get_update_delete(client: TestClient, admin: Headers, db: Session) -> None:
    project_id = new_project(client, admin)
    cap = post_ok(client, "/v1/capabilities", admin, {**BODY, "project_id": project_id})
    assert cap["id"].startswith("cap_")
    assert cap["higher_is_better"] is True
    assert cap["value_per_point"] == "25000.00"  # money is a string, never rounded

    updated = client.patch(
        f"/v1/capabilities/{cap['id']}", headers=admin, json={"value_per_point": "30000.50"}
    ).json()
    assert updated["value_per_point"] == "30000.50"
    assert updated["name"] == BODY["name"]

    assert client.delete(f"/v1/capabilities/{cap['id']}", headers=admin).status_code == 204
    assert client.get(f"/v1/capabilities/{cap['id']}", headers=admin).status_code == 404

    types = db.scalars(select(Event.type).where(Event.subject_id == cap["id"])).all()
    assert sorted(types) == ["capability.created", "capability.deleted", "capability.updated"]


def test_validation(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    for bad in (
        {"currency": "usd"},
        {"currency": "DOLLARS"},
        {"value_per_point": "-1"},
        {"value_per_point": "1.123456"},
        {"eval_metric": ""},
    ):
        response = client.post(
            "/v1/capabilities", headers=admin, json={**BODY, "project_id": project_id, **bad}
        )
        assert response.status_code == 422, bad


def test_admin_must_name_a_project(client: TestClient, admin: Headers) -> None:
    response = client.post("/v1/capabilities", headers=admin, json=BODY)
    assert response.status_code == 422
    assert "project_id is required" in response.json()["detail"]


def test_names_unique_per_project_only(client: TestClient, admin: Headers) -> None:
    a = new_project(client, admin, "A")
    b = new_project(client, admin, "B")
    post_ok(client, "/v1/capabilities", admin, {**BODY, "project_id": a})
    dup = client.post("/v1/capabilities", headers=admin, json={**BODY, "project_id": a})
    assert dup.status_code == 409
    post_ok(client, "/v1/capabilities", admin, {**BODY, "project_id": b})


def test_list_filters_by_project(client: TestClient, admin: Headers) -> None:
    a = new_project(client, admin, "A")
    b = new_project(client, admin, "B")
    post_ok(client, "/v1/capabilities", admin, {**BODY, "project_id": a})
    post_ok(client, "/v1/capabilities", admin, {**BODY, "project_id": b})
    assert len(client.get("/v1/capabilities", headers=admin).json()["data"]) == 2
    only_a = client.get(f"/v1/capabilities?project_id={a}", headers=admin).json()["data"]
    assert [c["project_id"] for c in only_a] == [a]
