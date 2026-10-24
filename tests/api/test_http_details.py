"""HTTP details the fuzz tests (tests/test_fuzz.py) turned up."""

from fastapi.testclient import TestClient

from tests.helpers import Headers


def test_405_lists_every_method_the_path_supports(client: TestClient, admin: Headers) -> None:
    response = client.request("PUT", "/v1/projects", headers=admin)
    assert response.status_code == 405
    assert response.headers["allow"] == "GET, POST"
    item = client.request("PUT", "/v1/projects/prj_x", headers=admin)
    assert item.headers["allow"] == "DELETE, GET, PATCH"


def test_unreadable_body_is_422_like_other_bad_input(client: TestClient, admin: Headers) -> None:
    response = client.post(
        "/v1/projects",
        headers={**admin, "Content-Type": "application/json"},
        content=b"\x19t\xff\xfe\x15",
    )
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "The request body isn't valid JSON text."


def test_nul_characters_are_refused_not_a_crash(client: TestClient, admin: Headers) -> None:
    in_query = client.get("/v1/webhook-endpoints?cursor=%00", headers=admin)
    assert in_query.status_code == 422
    assert "NUL" in in_query.json()["detail"]
    in_body = client.post("/v1/projects", headers=admin, json={"name": "bad\u0000name"})
    assert in_body.status_code == 422
