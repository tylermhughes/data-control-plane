from fastapi.testclient import TestClient

from tests.helpers import Headers, new_project, post_ok

KINDS = [
    "human_vendor",
    "expert_network",
    "synthetic",
    "rl_environment",
    "enterprise_workflow",
    "beta_users",
    "licensed_dataset",
]


def test_every_kind_with_default_units(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    for kind in KINDS:
        src = post_ok(
            client,
            "/v1/data-sources",
            admin,
            {"project_id": project_id, "name": kind, "kind": kind, "license_type": "other"},
        )
        assert src["id"].startswith("src_")
        assert src["default_unit"] == ("tasks" if kind == "rl_environment" else "items")


def test_rights_fields_round_trip(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    body = {
        "project_id": project_id,
        "name": "Carrier imagery archive",
        "kind": "licensed_dataset",
        "default_unit": "images",
        "license_type": "licensed",
        "consent_scope": "Training use only",
        "rights_expires_at": "2029-10-01",
        "pii_handling": "Addresses blurred by licensor",
        "notes": "3 years, no redistribution",
    }
    src = post_ok(client, "/v1/data-sources", admin, body)
    for field, value in body.items():
        assert src[field] == value

    cleared = client.patch(
        f"/v1/data-sources/{src['id']}", headers=admin, json={"rights_expires_at": None}
    ).json()
    assert cleared["rights_expires_at"] is None
    assert cleared["license_type"] == "licensed"


def test_rejects_unknown_kind_and_license(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    base = {"project_id": project_id, "name": "X", "kind": "synthetic", "license_type": "owned"}
    for bad in ({"kind": "crowd"}, {"license_type": "handshake"}, {"license_type": None}):
        response = client.post("/v1/data-sources", headers=admin, json={**base, **bad})
        assert response.status_code == 422, bad


def test_kind_cannot_change(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    src = post_ok(
        client,
        "/v1/data-sources",
        admin,
        {"project_id": project_id, "name": "S", "kind": "synthetic", "license_type": "owned"},
    )
    response = client.patch(
        f"/v1/data-sources/{src['id']}", headers=admin, json={"kind": "beta_users"}
    )
    assert response.status_code == 422
