"""M9 end to end: the generated client, the dcp CLI and the example scripts against a real
running server (uvicorn on a free port, the throwaway test database)."""

import json
import os
import socket
import subprocess
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import Headers, Setup, post_ok

ROOT = Path(__file__).parents[2]


@pytest.fixture
def server() -> Iterator[str]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not srv.started and time.time() < deadline:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True
    thread.join(timeout=5)


def run(args: list[str], url: str, key: str) -> subprocess.CompletedProcess[str]:
    """Run inside the CLI's own environment (which has the generated client)."""
    env = {**os.environ, "DCP_URL": url, "DCP_API_KEY": key}
    # A fixed command (uv) with arguments chosen by the test itself.
    return subprocess.run(  # noqa: S603
        ["uv", "run", "--quiet", "--project", str(ROOT / "clients/cli"), *args],  # noqa: S607
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def key_of(headers: Headers) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def test_cli_drives_the_api(server: str, admin: Headers) -> None:
    created = run(
        ["dcp", "projects", "create-project", "--body", '{"name": "From the CLI"}'],
        server,
        key_of(admin),
    )
    assert created.returncode == 0, created.stderr
    project = json.loads(created.stdout)
    assert project["name"] == "From the CLI"

    listed = run(["dcp", "projects", "list-projects", "--limit", "5"], server, key_of(admin))
    assert [p["id"] for p in json.loads(listed.stdout)["data"]] == [project["id"]]

    refused = run(
        ["dcp", "projects", "get-project", "--project-id", "prj_nope"], server, key_of(admin)
    )
    assert refused.returncode == 1
    assert json.loads(refused.stdout)["status"] == 404


def test_example_scripts(server: str, client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    batches: list[Any] = []
    for _ in range(2):
        b = s.batch(alloc["id"])
        batches.append(
            post_ok(client, f"/v1/batches/{b['id']}/accept", admin, {"accepted_count": 900})
        )
    ds = post_ok(client, "/v1/datasets", admin, {"capability_id": s.capability_id, "name": "d"})

    trained = run(
        [
            "python",
            "examples/record_training_run.py",
            "--dataset-id",
            ds["id"],
            "--batch-ids",
            ",".join(b["id"] for b in batches),
            "--value",
            "0.81",
            "--run-name",
            "run-1",
        ],
        server,
        key_of(admin),
    )
    assert trained.returncode == 0, trained.stdout + trained.stderr
    assert "Dataset version 1" in trained.stdout
    assert "Recorded recall@0.5 = 0.81" in trained.stdout
    assert "Diagnosis: not_enough_data" in trained.stdout

    version_id = trained.stdout.split("(")[1].split(")")[0]
    gate = run(
        ["python", "examples/quality_gate.py", "--dataset-version-id", version_id],
        server,
        key_of(admin),
    )
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "Gate passed" in gate.stdout

    past = "2020-01-01"
    client.patch(
        f"/v1/data-sources/{s.sources['Surge']}", headers=admin, json={"rights_expires_at": past}
    )
    gate = run(
        ["python", "examples/quality_gate.py", "--dataset-version-id", version_id],
        server,
        key_of(admin),
    )
    assert gate.returncode == 1
    assert "rights for Surge expired on 2020-01-01" in gate.stdout
