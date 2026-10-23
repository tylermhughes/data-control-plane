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
