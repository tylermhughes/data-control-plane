import logging

import pytest
from fastapi.testclient import TestClient

from app.cli import main
from app.main import app


def test_create_admin_key_prints_a_working_key(
    client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["create-admin-key", "--name", "first"]) == 0
    out = capsys.readouterr().out
    secret = next(line.strip() for line in out.splitlines() if line.strip().startswith("dcp_"))

    me = client.get("/v1/me", headers={"Authorization": f"Bearer {secret}"}).json()
    assert me["name"] == "first"
    assert me["role"] == "admin"
    assert me["access"] == "write"


def test_startup_hints_until_an_admin_key_exists(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING), TestClient(app):
        pass
    assert "create-admin-key" in caplog.text

    main(["create-admin-key"])
    caplog.clear()
    with caplog.at_level(logging.WARNING), TestClient(app):
        pass
    assert "create-admin-key" not in caplog.text
