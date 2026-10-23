from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from tests.helpers import SPEC_CONTENT, Headers, new_project, post_ok


def new_spec(client: TestClient, admin: Headers, content: dict[str, Any] | None = None) -> Any:
    project_id = new_project(client, admin)
    return post_ok(
        client,
        "/v1/specs",
        admin,
        {
            "project_id": project_id,
            "name": "Package damage",
            "first_version": content or SPEC_CONTENT,
        },
    )


def approve(client: TestClient, admin: Headers, spec_id: str, n: int) -> Any:
    return post_ok(
        client, f"/v1/specs/{spec_id}/versions/{n}/approve", admin, {"approved_by": "Priya Nair"}
    )


def test_create_makes_draft_v1(client: TestClient, admin: Headers) -> None:
    spec = new_spec(client, admin)
    assert spec["id"].startswith("spc_")
    assert (spec["latest_version"], spec["draft_version"], spec["latest_approved_version"]) == (
        1,
        1,
        None,
    )
    v1 = client.get(f"/v1/specs/{spec['id']}/versions/1", headers=admin).json()
    assert v1["status"] == "draft"
    assert v1["coverage_targets"] == SPEC_CONTENT["coverage_targets"]
    assert v1["acceptance_rules"][1]["applies_to"] == {"package_type": "shrink_wrapped"}


def test_approved_versions_are_frozen(client: TestClient, admin: Headers) -> None:
    spec = new_spec(client, admin)
    v1 = approve(client, admin, spec["id"], 1)
    assert v1["status"] == "approved"
    assert v1["approved_by"] == "Priya Nair"
    assert v1["approved_by_key_id"].startswith("key_")
    assert v1["approved_at"] is not None

    path = f"/v1/specs/{spec['id']}/versions/1"
    edit = client.patch(path, headers=admin, json={"guidelines": "changed"})
    assert edit.status_code == 409
    assert "Create a new version" in edit.json()["detail"]
    assert client.delete(path, headers=admin).status_code == 409
    again = client.post(f"{path}/approve", headers=admin, json={"approved_by": "Someone"})
    assert again.status_code == 409


def test_new_version_copies_latest_and_leaves_old_untouched(
    client: TestClient, admin: Headers
) -> None:
    spec = new_spec(client, admin)
    v1 = approve(client, admin, spec["id"], 1)

    new_targets = {"package_type": {"box": 0.2, "mailer": 0.3, "shrink_wrapped": 0.5}}
    v2 = post_ok(
        client,
        f"/v1/specs/{spec['id']}/versions",
        admin,
        {"coverage_targets": new_targets, "change_note": "More shrink-wrap."},
    )
    assert (v2["version"], v2["status"]) == (2, "draft")
    assert v2["coverage_targets"] == new_targets
    assert v2["attributes"] == v1["attributes"]  # copied
    assert v2["guidelines"] == v1["guidelines"]  # copied
    assert v2["change_note"] == "More shrink-wrap."

    assert client.get(f"/v1/specs/{spec['id']}/versions/1", headers=admin).json() == v1

    summary = client.get(f"/v1/specs/{spec['id']}", headers=admin).json()
    assert (summary["latest_version"], summary["draft_version"]) == (2, 2)
    assert summary["latest_approved_version"] == 1


def test_only_one_draft_at_a_time(client: TestClient, admin: Headers) -> None:
    spec = new_spec(client, admin)
    response = client.post(f"/v1/specs/{spec['id']}/versions", headers=admin, json={})
    assert response.status_code == 409
    assert "already has a draft" in response.json()["detail"]


def test_drafts_can_be_edited_and_discarded(client: TestClient, admin: Headers) -> None:
    spec = new_spec(client, admin)
    approve(client, admin, spec["id"], 1)
    post_ok(client, f"/v1/specs/{spec['id']}/versions", admin, {})
    path = f"/v1/specs/{spec['id']}/versions/2"

    edited = client.patch(path, headers=admin, json={"guidelines": "New rules."}).json()
    assert edited["guidelines"] == "New rules."
    kept = [{"name": a["name"], "values": a["values"]} for a in edited["attributes"]]
    assert kept == SPEC_CONTENT["attributes"]  # unchanged fields kept

    assert client.delete(path, headers=admin).status_code == 204
    assert client.get(path, headers=admin).status_code == 404


def test_only_version_cannot_be_discarded(client: TestClient, admin: Headers) -> None:
    spec = new_spec(client, admin)
    response = client.delete(f"/v1/specs/{spec['id']}/versions/1", headers=admin)
    assert response.status_code == 409


def test_content_is_cross_checked(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    attrs = SPEC_CONTENT["attributes"]
    cases = {
        "unknown attribute": {"attributes": attrs, "coverage_targets": {"colour": {"red": 0.5}}},
        "unknown value": {"attributes": attrs, "coverage_targets": {"zone": {"dock": 0.5}}},
        "over 100%": {
            "attributes": attrs,
            "coverage_targets": {"zone": {"induct": 0.7, "sort": 0.4}},
        },
        "share above 1": {"attributes": attrs, "coverage_targets": {"zone": {"induct": 1.5}}},
        "rule on unknown value": {
            "attributes": attrs,
            "acceptance_rules": [
                {
                    "metric": "agreement",
                    "operator": ">=",
                    "threshold": 1,
                    "applies_to": {"zone": "x"},
                }
            ],
        },
        "duplicate attribute": {"attributes": [attrs[0], attrs[0]]},
        "duplicate value": {"attributes": [{"name": "a", "values": ["x", "x"]}]},
        "bad attribute name": {"attributes": [{"name": "Package Type", "values": ["x"]}]},
        "bad operator": {"acceptance_rules": [{"metric": "m", "operator": "~", "threshold": 1}]},
    }
    for label, content in cases.items():
        response = client.post(
            "/v1/specs",
            headers=admin,
            json={"project_id": project_id, "name": label, "first_version": content},
        )
        assert response.status_code == 422, label


def test_draft_edits_are_cross_checked_against_merged_content(
    client: TestClient, admin: Headers
) -> None:
    spec = new_spec(client, admin)
    path = f"/v1/specs/{spec['id']}/versions/1"
    # Dropping an attribute that coverage targets still use is refused...
    response = client.patch(
        path, headers=admin, json={"attributes": [SPEC_CONTENT["attributes"][1]]}
    )
    assert response.status_code == 422
    assert "unknown attribute 'package_type'" in response.json()["detail"]
    # ...unless the targets are updated in the same edit.
    ok = client.patch(
        path,
        headers=admin,
        json={
            "attributes": [SPEC_CONTENT["attributes"][1]],
            "coverage_targets": {"zone": {"induct": 0.6}},
            "acceptance_rules": [],
        },
    )
    assert ok.status_code == 200, ok.text


def test_lifecycle_events(client: TestClient, admin: Headers, db: Session) -> None:
    spec = new_spec(client, admin)
    approve(client, admin, spec["id"], 1)
    post_ok(client, f"/v1/specs/{spec['id']}/versions", admin, {})
    types = db.scalars(
        select(Event.type).where(Event.project_id == spec["project_id"]).order_by(Event.id)
    ).all()
    assert types[-4:] == [
        "spec.created",
        "spec_version.created",
        "spec_version.approved",
        "spec_version.created",
    ]


def test_delete_spec_removes_versions(client: TestClient, admin: Headers) -> None:
    spec = new_spec(client, admin)
    approve(client, admin, spec["id"], 1)
    assert client.delete(f"/v1/specs/{spec['id']}", headers=admin).status_code == 204
    assert client.get(f"/v1/specs/{spec['id']}/versions/1", headers=admin).status_code == 404
