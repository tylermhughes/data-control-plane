"""Project keys work inside their own project only, for every project-scoped resource."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MakeKey
from tests.helpers import SPEC_CONTENT, Headers, new_project, post_ok

RESOURCES: dict[str, dict[str, Any]] = {
    "/v1/capabilities": {
        "name": "Damage",
        "eval_metric": "recall",
        "value_per_point": "100",
        "currency": "USD",
    },
    "/v1/data-sources": {
        "name": "Surge",
        "kind": "human_vendor",
        "license_type": "vendor_agreement",
    },
    "/v1/specs": {"name": "Damage spec", "first_version": SPEC_CONTENT},
}


@pytest.mark.parametrize("path", RESOURCES)
def test_project_key_defaults_to_and_stays_in_its_project(
    path: str, client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    mine = new_project(client, admin, "Mine")
    theirs = new_project(client, admin, "Theirs")
    writer = make_key(role="project", project_id=mine)
    body = RESOURCES[path]

    own = post_ok(client, path, writer, body)  # no project_id: goes into the key's project
    assert own["project_id"] == mine

    other = post_ok(client, path, admin, {**body, "project_id": theirs})
    assert client.get(f"{path}/{other['id']}", headers=writer).status_code == 404
    assert (
        client.patch(f"{path}/{other['id']}", headers=writer, json={"name": "x"}).status_code == 404
    )
    assert client.delete(f"{path}/{other['id']}", headers=writer).status_code == 404
    listed = client.get(path, headers=writer).json()["data"]
    assert [item["id"] for item in listed] == [own["id"]]
    listed_other = client.get(f"{path}?project_id={theirs}", headers=writer).json()["data"]
    assert listed_other == []

    sneaky = client.post(path, headers=writer, json={**body, "name": "n2", "project_id": theirs})
    assert sneaky.status_code == 422


@pytest.mark.parametrize("path", RESOURCES)
def test_read_only_project_key_cannot_write(
    path: str, client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    project_id = new_project(client, admin)
    reader = make_key(role="project", access="read", project_id=project_id)
    assert client.get(path, headers=reader).status_code == 200
    assert client.post(path, headers=reader, json=RESOURCES[path]).status_code == 403


def test_project_with_contents_cannot_be_deleted(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin)
    src = post_ok(
        client,
        "/v1/data-sources",
        admin,
        {**RESOURCES["/v1/data-sources"], "project_id": project_id},
    )
    response = client.delete(f"/v1/projects/{project_id}", headers=admin)
    assert response.status_code == 409
    assert "data sources" in response.json()["detail"]

    client.delete(f"/v1/data-sources/{src['id']}", headers=admin)
    assert client.delete(f"/v1/projects/{project_id}", headers=admin).status_code == 204
