from fastapi.testclient import TestClient

from tests.conftest import MakeKey


def test_missing_key_is_401_problem(client: TestClient) -> None:
    response = client.get("/v1/projects")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["www-authenticate"] == "Bearer"
    body = response.json()
    assert body["status"] == 401
    assert body["title"] == "Unauthorized"
    assert "Missing API key" in body["detail"]


def test_wrong_key_is_401(client: TestClient) -> None:
    for bad in ("dcp_not-a-real-key", "not-even-the-right-format"):
        response = client.get("/v1/projects", headers={"Authorization": f"Bearer {bad}"})
        assert response.status_code == 401


def test_revoked_key_stops_working(client: TestClient, admin: dict[str, str]) -> None:
    created = client.post(
        "/v1/api-keys", headers=admin, json={"name": "temp", "role": "admin"}
    ).json()
    temp = {"Authorization": f"Bearer {created['secret']}"}
    assert client.get("/v1/me", headers=temp).status_code == 200

    assert client.delete(f"/v1/api-keys/{created['id']}", headers=admin).status_code == 204
    assert client.get("/v1/me", headers=temp).status_code == 401


def test_me_describes_the_key(client: TestClient, make_key: MakeKey) -> None:
    reader = make_key(access="read")
    body = client.get("/v1/me", headers=reader).json()
    assert body["role"] == "admin"
    assert body["access"] == "read"
    assert body["key_prefix"].startswith("dcp_")
    assert "secret" not in body
    assert body["last_used_at"] is not None


def test_read_only_key_cannot_write(client: TestClient, make_key: MakeKey) -> None:
    reader = make_key(access="read")
    assert client.get("/v1/projects", headers=reader).status_code == 200
    response = client.post("/v1/projects", headers=reader, json={"name": "x"})
    assert response.status_code == 403
    assert response.json()["detail"] == "This API key is read-only."
