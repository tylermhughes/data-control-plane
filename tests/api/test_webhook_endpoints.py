from fastapi.testclient import TestClient

from tests.conftest import MakeKey
from tests.helpers import Headers, new_project, post_ok

URL = "https://hooks.example.com/dcp"


def test_create_shows_secret_and_secret_endpoint_agrees(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    ep = post_ok(
        client,
        "/v1/webhook-endpoints",
        admin,
        {"project_id": project_id, "url": URL, "event_types": ["batch.*"]},
    )
    assert ep["id"].startswith("whk_")
    assert ep["secret"].startswith("whsec_")
    assert (ep["enabled"], ep["secret_version"], ep["event_types"]) == (True, 1, ["batch.*"])

    shown = client.get(f"/v1/webhook-endpoints/{ep['id']}/secret", headers=admin).json()
    assert shown == {"secret": ep["secret"], "previous_secret_valid_until": None}
    fetched = client.get(f"/v1/webhook-endpoints/{ep['id']}", headers=admin).json()
    assert "secret" not in fetched


def test_rotation_gives_a_new_secret_with_overlap(client: TestClient, admin: Headers) -> None:
    ep = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL})
    rotated = client.post(f"/v1/webhook-endpoints/{ep['id']}/rotate-secret", headers=admin).json()
    assert rotated["secret"] != ep["secret"]
    assert rotated["previous_secret_valid_until"] is not None
    after = client.get(f"/v1/webhook-endpoints/{ep['id']}", headers=admin).json()
    assert after["secret_version"] == 2


def test_admin_without_project_makes_org_wide_endpoint(client: TestClient, admin: Headers) -> None:
    ep = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL})
    assert ep["project_id"] is None
    assert ep["event_types"] == ["*"]


def test_project_keys_stay_in_their_project(
    client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    mine = new_project(client, admin, "Mine")
    theirs = new_project(client, admin, "Theirs")
    key = make_key(role="project", project_id=mine)

    own = post_ok(client, "/v1/webhook-endpoints", key, {"url": URL})
    assert own["project_id"] == mine  # defaults to the key's project, never org-wide

    org_wide = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL})
    other = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL, "project_id": theirs})
    for hidden in (org_wide, other):
        assert client.get(f"/v1/webhook-endpoints/{hidden['id']}", headers=key).status_code == 404
    listed = client.get("/v1/webhook-endpoints", headers=key).json()["data"]
    assert [e["id"] for e in listed] == [own["id"]]
    sneaky = client.post(
        "/v1/webhook-endpoints", headers=key, json={"url": URL, "project_id": theirs}
    )
    assert sneaky.status_code == 422


def test_read_only_keys_cannot_see_secrets(
    client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    ep = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL})
    reader = make_key(access="read")
    assert client.get(f"/v1/webhook-endpoints/{ep['id']}", headers=reader).status_code == 200
    assert client.get(f"/v1/webhook-endpoints/{ep['id']}/secret", headers=reader).status_code == 403


def test_validation(client: TestClient, admin: Headers) -> None:
    for bad in (
        {"url": "ftp://example.com"},
        {"url": "http://169.254.169.254/latest/meta-data/"},
        {"url": URL, "event_types": ["Batch Accepted"]},
        {"url": URL, "event_types": []},
    ):
        assert client.post("/v1/webhook-endpoints", headers=admin, json=bad).status_code == 422, bad
    ep = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL})
    patch = client.patch(
        f"/v1/webhook-endpoints/{ep['id']}", headers=admin, json={"url": "file:///etc/passwd"}
    )
    assert patch.status_code == 422


def test_update_and_delete(client: TestClient, admin: Headers) -> None:
    ep = post_ok(client, "/v1/webhook-endpoints", admin, {"url": URL})
    path = f"/v1/webhook-endpoints/{ep['id']}"
    paused = client.patch(path, headers=admin, json={"enabled": False}).json()
    assert paused["enabled"] is False
    assert client.delete(path, headers=admin).status_code == 204
    assert client.get(path, headers=admin).status_code == 404


def test_event_log_api(client: TestClient, admin: Headers, make_key: MakeKey) -> None:
    mine = new_project(client, admin, "Mine")
    new_project(client, admin, "Theirs")
    events = client.get("/v1/events?type=project.*", headers=admin).json()["data"]
    assert [e["type"] for e in events] == ["project.created", "project.created"]
    by_subject = client.get(f"/v1/events?subject_id={mine}", headers=admin).json()["data"]
    assert [e["data"]["name"] for e in by_subject] == ["Mine"]

    key = make_key(role="project", project_id=mine)
    visible = client.get("/v1/events", headers=key).json()["data"]
    assert {e["project_id"] for e in visible} == {mine}
    assert client.get(f"/v1/events/{events[1]['id']}", headers=key).status_code == 404
