"""Things in use by requests or allocations can't be deleted, and the error says what uses them."""

from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup, post_ok


def test_capability_used_by_request(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.request()
    response = client.delete(f"/v1/capabilities/{s.capability_id}", headers=admin)
    assert response.status_code == 409
    assert req["id"] in response.json()["detail"]


def test_source_used_by_allocation(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.allocate(s.request()["id"], "Surge")
    response = client.delete(f"/v1/data-sources/{s.sources['Surge']}", headers=admin)
    assert response.status_code == 409
    assert alloc["id"] in response.json()["detail"]
    unused = client.delete(f"/v1/data-sources/{s.sources['Mercor']}", headers=admin)
    assert unused.status_code == 204


def test_spec_used_by_request(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    req = s.request()
    response = client.delete(f"/v1/specs/{s.spec_id}", headers=admin)
    assert response.status_code == 409
    assert req["id"] in response.json()["detail"]


def test_spec_draft_used_by_request(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    draft = post_ok(client, f"/v1/specs/{s.spec_id}/versions", admin, {})
    s.request(spec_version_id=draft["id"])
    response = client.delete(f"/v1/specs/{s.spec_id}/versions/2", headers=admin)
    assert response.status_code == 409


def test_long_lists_are_shortened(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    for _ in range(5):
        s.request()
    detail = client.delete(f"/v1/capabilities/{s.capability_id}", headers=admin).json()["detail"]
    assert detail.count("req_") == 3
    assert ", ..." in detail
