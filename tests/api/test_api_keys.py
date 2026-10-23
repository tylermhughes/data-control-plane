from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApiKey, Event
from tests.conftest import MakeKey


def test_create_shows_secret_once_and_stores_only_a_hash(
    client: TestClient, admin: dict[str, str], db: Session
) -> None:
    response = client.post("/v1/api-keys", headers=admin, json={"name": "CI", "role": "admin"})
    assert response.status_code == 201
    created = response.json()
    secret = created["secret"]
    assert secret.startswith("dcp_") and len(secret) > 40
    assert created["key_prefix"] == secret[:12]

    fetched = client.get(f"/v1/api-keys/{created['id']}", headers=admin).json()
    assert "secret" not in fetched
    listed = client.get("/v1/api-keys", headers=admin).json()["data"]
    assert all("secret" not in k for k in listed)

    row = db.get_one(ApiKey, created["id"])
    assert secret not in (row.key_hash, row.key_prefix)


def test_secret_never_appears_in_events(
    client: TestClient, admin: dict[str, str], db: Session
) -> None:
    secret = client.post(
        "/v1/api-keys", headers=admin, json={"name": "CI", "role": "admin"}
    ).json()["secret"]
    for event in db.scalars(select(Event)).all():
        assert secret not in str(event.data)


def test_project_key_requires_existing_project(client: TestClient, admin: dict[str, str]) -> None:
    missing = client.post("/v1/api-keys", headers=admin, json={"name": "x", "role": "project"})
    assert missing.status_code == 422

    unknown = client.post(
        "/v1/api-keys",
        headers=admin,
        json={"name": "x", "role": "project", "project_id": "prj_nope"},
    )
    assert unknown.status_code == 422
    assert "No project" in unknown.json()["detail"]

    admin_with_project = client.post(
        "/v1/api-keys",
        headers=admin,
        json={"name": "x", "role": "admin", "project_id": "prj_nope"},
    )
    assert admin_with_project.status_code == 422


def test_only_admins_manage_keys(
    client: TestClient, admin: dict[str, str], make_key: MakeKey
) -> None:
    project = client.post("/v1/projects", headers=admin, json={"name": "P"}).json()
    scoped = make_key(role="project", project_id=project["id"])
    assert client.get("/v1/api-keys", headers=scoped).status_code == 403
    response = client.post("/v1/api-keys", headers=scoped, json={"name": "x", "role": "admin"})
    assert response.status_code == 403


def test_rename_and_revoke(client: TestClient, admin: dict[str, str], db: Session) -> None:
    created = client.post(
        "/v1/api-keys", headers=admin, json={"name": "old", "role": "admin", "access": "read"}
    ).json()
    renamed = client.patch(
        f"/v1/api-keys/{created['id']}", headers=admin, json={"name": "new"}
    ).json()
    assert renamed["name"] == "new"

    assert client.delete(f"/v1/api-keys/{created['id']}", headers=admin).status_code == 204
    assert client.delete(f"/v1/api-keys/{created['id']}", headers=admin).status_code == 204
    fetched = client.get(f"/v1/api-keys/{created['id']}", headers=admin).json()
    assert fetched["revoked_at"] is not None

    types = db.scalars(
        select(Event.type).where(Event.subject_id == created["id"]).order_by(Event.id)
    ).all()
    assert types == ["api_key.created", "api_key.updated", "api_key.revoked"]


def test_cannot_revoke_last_admin_writer(client: TestClient, admin: dict[str, str]) -> None:
    me = client.get("/v1/me", headers=admin).json()
    response = client.delete(f"/v1/api-keys/{me['id']}", headers=admin)
    assert response.status_code == 409
    assert "last active admin key" in response.json()["detail"]

    client.post("/v1/api-keys", headers=admin, json={"name": "backup", "role": "admin"})
    assert client.delete(f"/v1/api-keys/{me['id']}", headers=admin).status_code == 204


def test_unknown_key_is_404(client: TestClient, admin: dict[str, str]) -> None:
    assert client.get("/v1/api-keys/key_nope", headers=admin).status_code == 404
