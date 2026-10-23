from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Project


def test_retry_with_same_key_returns_original(
    client: TestClient, admin: dict[str, str], db: Session
) -> None:
    headers = {**admin, "Idempotency-Key": "abc-123"}
    first = client.post("/v1/projects", headers=headers, json={"name": "Once"})
    second = client.post("/v1/projects", headers=headers, json={"name": "Once"})

    assert first.status_code == second.status_code == 201
    assert second.json() == first.json()
    assert second.headers["idempotent-replayed"] == "true"
    assert db.scalar(select(func.count()).select_from(Project)) == 1


def test_same_key_different_request_is_rejected(client: TestClient, admin: dict[str, str]) -> None:
    headers = {**admin, "Idempotency-Key": "abc-123"}
    client.post("/v1/projects", headers=headers, json={"name": "A"})
    response = client.post("/v1/projects", headers=headers, json={"name": "B"})
    assert response.status_code == 422
    assert "different request" in response.json()["detail"]


def test_without_header_each_post_is_new(client: TestClient, admin: dict[str, str]) -> None:
    client.post("/v1/projects", headers=admin, json={"name": "A"})
    assert client.post("/v1/projects", headers=admin, json={"name": "A"}).status_code == 409


def test_failed_request_is_not_remembered(client: TestClient, admin: dict[str, str]) -> None:
    client.post("/v1/projects", headers=admin, json={"name": "Taken"})
    headers = {**admin, "Idempotency-Key": "retry-me"}
    assert client.post("/v1/projects", headers=headers, json={"name": "Taken"}).status_code == 409

    # Once the conflict is fixed, a retry with the same key succeeds.
    taken = client.get("/v1/projects", headers=admin).json()["data"][0]
    client.patch(f"/v1/projects/{taken['id']}", headers=admin, json={"name": "Renamed"})
    assert client.post("/v1/projects", headers=headers, json={"name": "Taken"}).status_code == 201


def test_api_key_replay_does_not_reveal_secret(client: TestClient, admin: dict[str, str]) -> None:
    headers = {**admin, "Idempotency-Key": "key-1"}
    body = {"name": "CI", "role": "admin"}
    first = client.post("/v1/api-keys", headers=headers, json=body).json()
    second = client.post("/v1/api-keys", headers=headers, json=body).json()
    assert "secret" in first
    assert "secret" not in second
    assert second["id"] == first["id"]


def test_header_must_look_like_a_key(client: TestClient, admin: dict[str, str]) -> None:
    pasted_json = '{"name": "Fulfillment vision"}'
    response = client.post(
        "/v1/projects", headers={**admin, "Idempotency-Key": pasted_json}, json={"name": "X"}
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "header.idempotency-key"
    assert db_has_no_projects(client, admin)

    ok = client.post(
        "/v1/projects", headers={**admin, "Idempotency-Key": "ci-run-42"}, json={"name": "X"}
    )
    assert ok.status_code == 201


def db_has_no_projects(client: TestClient, admin: dict[str, str]) -> bool:
    return client.get("/v1/projects", headers=admin).json()["data"] == []
