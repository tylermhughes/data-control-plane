"""Small helpers shared by API tests."""

from typing import Any

from fastapi.testclient import TestClient

Headers = dict[str, str]


def post_ok(client: TestClient, path: str, headers: Headers, body: dict[str, Any]) -> Any:
    response = client.post(path, headers=headers, json=body)
    assert response.status_code in (200, 201), response.text
    return response.json()


def new_project(client: TestClient, admin: Headers, name: str = "Vision") -> str:
    project_id: str = post_ok(client, "/v1/projects", admin, {"name": name})["id"]
    return project_id


SPEC_CONTENT: dict[str, Any] = {
    "guidelines": "Label every damaged area at least 12 px across.",
    "attributes": [
        {"name": "package_type", "values": ["box", "mailer", "shrink_wrapped"]},
        {"name": "zone", "values": ["induct", "sort"]},
    ],
    "coverage_targets": {
        "package_type": {"box": 0.3, "mailer": 0.35, "shrink_wrapped": 0.35},
        "zone": {"induct": 0.6},
    },
    "acceptance_rules": [
        {"metric": "agreement", "operator": ">=", "threshold": 0.85},
        {
            "metric": "agreement",
            "operator": ">=",
            "threshold": 0.8,
            "applies_to": {"package_type": "shrink_wrapped"},
        },
    ],
    "change_note": "First version.",
}


class Setup:
    """A project with a capability, three sources and an approved spec (v1)."""

    def __init__(self, client: TestClient, admin: Headers, name: str = "Vision") -> None:
        self.client, self.admin = client, admin
        self.project_id = new_project(client, admin, name)
        self.capability_id = post_ok(
            client,
            "/v1/capabilities",
            admin,
            {
                "project_id": self.project_id,
                "name": "Damage",
                "eval_metric": "recall@0.5",
                "value_per_point": "25000",
                "currency": "USD",
            },
        )["id"]
        self.sources = {
            name: post_ok(
                client,
                "/v1/data-sources",
                admin,
                {
                    "project_id": self.project_id,
                    "name": name,
                    "kind": kind,
                    "default_unit": unit,
                    "license_type": "other",
                },
            )["id"]
            for name, kind, unit in (
                ("Surge", "human_vendor", "images"),
                ("Mercor", "human_vendor", "images"),
                ("Returns photos", "enterprise_workflow", "images"),
                ("Picking sim", "rl_environment", "tasks"),
            )
        }
        spec = post_ok(
            client,
            "/v1/specs",
            admin,
            {"project_id": self.project_id, "name": "Damage spec", "first_version": SPEC_CONTENT},
        )
        self.spec_id = spec["id"]
        self.v1 = post_ok(
            client, f"/v1/specs/{self.spec_id}/versions/1/approve", admin, {"approved_by": "PM"}
        )["id"]

    def request(self, **extra: Any) -> Any:
        body = {
            "capability_id": self.capability_id,
            "title": "Shrink-wrap",
            "quantity": 10000,
            "unit": "images",
            "spec_version_id": self.v1,
            **extra,
        }
        return post_ok(self.client, "/v1/requests", self.admin, body)

    def open_request(self, **extra: Any) -> Any:
        req = self.request(**extra)
        return post_ok(self.client, f"/v1/requests/{req['id']}/open", self.admin, {})

    def allocate(self, request_id: str, source: str, **extra: Any) -> Any:
        body = {
            "request_id": request_id,
            "data_source_id": self.sources[source],
            "quantity": 4000,
            "quoted_unit_rate": "1.55",
            "currency": "USD",
            **extra,
        }
        return post_ok(self.client, "/v1/allocations", self.admin, body)

    def act(self, kind: str, obj_id: str, action: str) -> Any:
        return self.client.post(f"/v1/{kind}/{obj_id}/{action}", headers=self.admin)

    def active_allocation(self, source: str = "Surge", **extra: Any) -> Any:
        """An active allocation on an open request (4000 units at 1.55)."""
        req = self.open_request()
        alloc = self.allocate(req["id"], source, **extra)
        return self.act("allocations", alloc["id"], "activate").json()

    def batch(self, allocation_id: str, **extra: Any) -> Any:
        body = {"allocation_id": allocation_id, "delivered_count": 1000, "spend": "1550", **extra}
        return post_ok(self.client, "/v1/batches", self.admin, body)
