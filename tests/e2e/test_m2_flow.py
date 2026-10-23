"""M2 end to end: the steps Tyler follows in /docs, through the real API and database."""

from fastapi.testclient import TestClient

from tests.helpers import Headers, new_project, post_ok


def test_m2_capability_source_and_spec_lifecycle(client: TestClient, admin: Headers) -> None:
    project_id = new_project(client, admin, "Fulfillment vision")

    # 1. A capability with a value per eval point.
    cap = post_ok(
        client,
        "/v1/capabilities",
        admin,
        {
            "project_id": project_id,
            "name": "Package damage detection",
            "eval_metric": "recall@0.5",
            "value_per_point": "25000.00",
            "currency": "USD",
        },
    )
    assert cap["value_per_point"] == "25000.00"

    # 2. A data source with rights fields.
    src = post_ok(
        client,
        "/v1/data-sources",
        admin,
        {
            "project_id": project_id,
            "name": "Surge",
            "kind": "human_vendor",
            "default_unit": "images",
            "license_type": "vendor_agreement",
            "rights_expires_at": "2028-12-31",
        },
    )
    assert src["license_type"] == "vendor_agreement"

    # 3. A spec: v1 draft, approved.
    spec = post_ok(
        client,
        "/v1/specs",
        admin,
        {
            "project_id": project_id,
            "name": "Package damage",
            "first_version": {
                "attributes": [{"name": "package_type", "values": ["box", "shrink_wrapped"]}],
                "coverage_targets": {"package_type": {"box": 0.65, "shrink_wrapped": 0.35}},
            },
        },
    )
    v1 = post_ok(
        client, f"/v1/specs/{spec['id']}/versions/1/approve", admin, {"approved_by": "Priya Nair"}
    )

    # 4. v2 changes a coverage target; v1 is untouched and can't be edited.
    v2 = post_ok(
        client,
        f"/v1/specs/{spec['id']}/versions",
        admin,
        {"coverage_targets": {"package_type": {"box": 0.5, "shrink_wrapped": 0.5}}},
    )
    assert v2["version"] == 2
    assert client.get(f"/v1/specs/{spec['id']}/versions/1", headers=admin).json() == v1
    frozen = client.patch(
        f"/v1/specs/{spec['id']}/versions/1", headers=admin, json={"guidelines": "x"}
    )
    assert frozen.status_code == 409
