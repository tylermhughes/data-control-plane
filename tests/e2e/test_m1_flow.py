"""M1 end to end: the same steps Tyler follows in /docs, through the real API and database."""

import pytest
from fastapi.testclient import TestClient

from app.cli import main


def test_m1_first_admin_key_to_scoped_project_key(
    client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    # 1. No key: refused.
    assert client.get("/v1/projects").status_code == 401

    # 2. Create the first admin key with the server command.
    main(["create-admin-key"])
    out = capsys.readouterr().out
    secret = next(line.strip() for line in out.splitlines() if line.strip().startswith("dcp_"))
    admin = {"Authorization": f"Bearer {secret}"}

    # 3. Create two projects and list them.
    vision = client.post("/v1/projects", headers=admin, json={"name": "Vision"}).json()
    client.post("/v1/projects", headers=admin, json={"name": "Robotics"})
    assert len(client.get("/v1/projects", headers=admin).json()["data"]) == 2

    # 4. A read-only key for one project sees only that project and cannot write.
    key = client.post(
        "/v1/api-keys",
        headers=admin,
        json={"name": "dashboard", "role": "project", "access": "read", "project_id": vision["id"]},
    ).json()
    scoped = {"Authorization": f"Bearer {key['secret']}"}
    assert [p["name"] for p in client.get("/v1/projects", headers=scoped).json()["data"]] == [
        "Vision"
    ]
    assert client.post("/v1/projects", headers=scoped, json={"name": "X"}).status_code == 403

    # 5. Revoke it: it stops working.
    client.delete(f"/v1/api-keys/{key['id']}", headers=admin)
    assert client.get("/v1/projects", headers=scoped).status_code == 401
