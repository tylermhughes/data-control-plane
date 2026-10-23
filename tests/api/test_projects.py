from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from tests.conftest import MakeKey


def create(client: TestClient, headers: dict[str, str], name: str, **extra: str) -> dict[str, str]:
    response = client.post("/v1/projects", headers=headers, json={"name": name, **extra})
    assert response.status_code == 201, response.text
    body: dict[str, str] = response.json()
    return body


def test_create_get_update_delete(client: TestClient, admin: dict[str, str]) -> None:
    project = create(client, admin, "Fulfillment vision", description="Warehouse models")
    assert project["id"].startswith("prj_")
    assert project["description"] == "Warehouse models"

    assert client.get(f"/v1/projects/{project['id']}", headers=admin).json() == project

    updated = client.patch(
        f"/v1/projects/{project['id']}", headers=admin, json={"name": "Fulfillment CV"}
    ).json()
    assert updated["name"] == "Fulfillment CV"
    assert updated["description"] == "Warehouse models"  # untouched

    assert client.delete(f"/v1/projects/{project['id']}", headers=admin).status_code == 204
    assert client.get(f"/v1/projects/{project['id']}", headers=admin).status_code == 404


def test_names_are_unique(client: TestClient, admin: dict[str, str]) -> None:
    create(client, admin, "Robotics")
    response = client.post("/v1/projects", headers=admin, json={"name": "Robotics"})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

    other = create(client, admin, "Other")
    rename = client.patch(f"/v1/projects/{other['id']}", headers=admin, json={"name": "Robotics"})
    assert rename.status_code == 409


def test_validation_errors_are_problems(client: TestClient, admin: dict[str, str]) -> None:
    response = client.post("/v1/projects", headers=admin, json={"name": "", "colour": "red"})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    fields = {e["field"] for e in response.json()["errors"]}
    assert fields == {"body.name", "body.colour"}


def test_list_is_paginated(client: TestClient, admin: dict[str, str]) -> None:
    ids = [create(client, admin, f"Project {i}")["id"] for i in range(5)]

    page1 = client.get("/v1/projects?limit=2", headers=admin).json()
    page2 = client.get(f"/v1/projects?limit=2&cursor={page1['next_cursor']}", headers=admin).json()
    page3 = client.get(f"/v1/projects?limit=2&cursor={page2['next_cursor']}", headers=admin).json()

    seen = [p["id"] for page in (page1, page2, page3) for p in page["data"]]
    assert seen == sorted(ids)
    assert page3["next_cursor"] is None


def test_project_key_sees_only_its_project(
    client: TestClient, admin: dict[str, str], make_key: MakeKey
) -> None:
    mine = create(client, admin, "Mine")
    theirs = create(client, admin, "Theirs")
    scoped = make_key(role="project", project_id=mine["id"])

    listed = client.get("/v1/projects", headers=scoped).json()["data"]
    assert [p["id"] for p in listed] == [mine["id"]]
    assert client.get(f"/v1/projects/{mine['id']}", headers=scoped).status_code == 200
    assert client.get(f"/v1/projects/{theirs['id']}", headers=scoped).status_code == 404


def test_project_key_cannot_manage_projects(
    client: TestClient, admin: dict[str, str], make_key: MakeKey
) -> None:
    mine = create(client, admin, "Mine")
    scoped = make_key(role="project", project_id=mine["id"])
    assert client.post("/v1/projects", headers=scoped, json={"name": "New"}).status_code == 403
    rename = client.patch(f"/v1/projects/{mine['id']}", headers=scoped, json={"name": "X"})
    assert rename.status_code == 403
    assert client.delete(f"/v1/projects/{mine['id']}", headers=scoped).status_code == 403


def test_cannot_delete_project_with_active_keys(client: TestClient, admin: dict[str, str]) -> None:
    project = create(client, admin, "Busy")
    key = client.post(
        "/v1/api-keys",
        headers=admin,
        json={"name": "ci", "role": "project", "project_id": project["id"]},
    ).json()

    response = client.delete(f"/v1/projects/{project['id']}", headers=admin)
    assert response.status_code == 409
    assert "Revoke them first" in response.json()["detail"]

    client.delete(f"/v1/api-keys/{key['id']}", headers=admin)
    assert client.delete(f"/v1/projects/{project['id']}", headers=admin).status_code == 204


def test_every_change_records_an_event(
    client: TestClient, admin: dict[str, str], db: Session
) -> None:
    project = create(client, admin, "Audited")
    client.patch(f"/v1/projects/{project['id']}", headers=admin, json={"description": "d"})
    client.delete(f"/v1/projects/{project['id']}", headers=admin)

    rows = db.scalars(
        select(Event).where(Event.subject_id == project["id"]).order_by(Event.id)
    ).all()
    assert [e.type for e in rows] == ["project.created", "project.updated", "project.deleted"]
    assert rows[0].data["name"] == "Audited"
    assert all(e.actor_key_id and e.actor_key_id.startswith("key_") for e in rows)


def test_failed_change_records_no_event(
    client: TestClient, admin: dict[str, str], db: Session
) -> None:
    create(client, admin, "Taken")
    client.post("/v1/projects", headers=admin, json={"name": "Taken"})
    assert len(db.scalars(select(Event).where(Event.type == "project.created")).all()) == 1
