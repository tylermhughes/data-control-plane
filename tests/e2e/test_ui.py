"""Browser tests for the web interface (web/e2e/*.spec.ts), run with Playwright's official
Docker image against a real DCP serving the built UI, with demo data seeded.

Skipped unless the UI has been built (./scripts/web.sh run build; check.sh does it)."""

import importlib.util
import os
import shutil
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
from sqlalchemy.orm import Session

from app.main import create_app
from app.worker.__main__ import run_once
from tests.helpers import Headers

ROOT = Path(__file__).parents[2]
DIST = ROOT / "web" / "dist"
PLAYWRIGHT_IMAGE = "mcr.microsoft.com/playwright:v1.64.0-noble"

pytestmark = pytest.mark.skipif(
    not (DIST / "index.html").is_file() or shutil.which("docker") is None,
    reason="web interface not built (./scripts/web.sh run build) or Docker not available",
)


@pytest.fixture
def ui_server() -> Iterator[int]:
    with socket.socket() as s:
        s.bind(("0.0.0.0", 0))  # noqa: S104 (the Playwright container must reach it)
        port = int(s.getsockname()[1])
    app = create_app(web_dir=str(DIST))
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning"))  # noqa: S104
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    yield port
    server.should_exit = True
    thread.join(timeout=5)


def seed_demo(client: TestClient, admin: Headers, db: Session, data_dir: Path) -> Any:
    """The north-star demo, plus one delivery still waiting for a decision (for the board)."""
    spec = importlib.util.spec_from_file_location("demo", ROOT / "scripts" / "demo.py")
    assert spec and spec.loader
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)

    def api(method: str, path: str, body: Any = None) -> Any:
        run_once(db)
        response = client.request(method, path, json=body, headers=admin)
        assert response.status_code < 400, f"{method} {path}: {response.text}"
        return response.json() if response.content else None

    seeded = demo.run(
        api,
        webhook_port=None,
        say=lambda _: None,
        data_dir=data_dir,
        uri_root=str(data_dir),
        diagnosis=True,
    )
    pid = seeded["project_id"]
    requests = api("GET", f"/v1/requests?project_id={pid}")["data"]
    sources = api("GET", f"/v1/data-sources?project_id={pid}")["data"]
    next_round = next(r["id"] for r in requests if r["title"] == "Next round")
    api("POST", f"/v1/requests/{next_round}/open")
    allocation = api(
        "POST",
        "/v1/allocations",
        {
            "request_id": next_round,
            "data_source_id": next(s["id"] for s in sources if s["name"] == "Surge"),
            "quantity": 2000,
            "quoted_unit_rate": "1.55",
            "currency": "USD",
        },
    )
    api("POST", f"/v1/allocations/{allocation['id']}/activate")
    api(
        "POST",
        "/v1/batches",
        {"allocation_id": allocation["id"], "delivered_count": 500, "spend": "775"},
    )
    return seeded


def test_web_interface_in_a_real_browser(
    ui_server: int, client: TestClient, admin: Headers, db: Session, data_dir: Path
) -> None:
    seeded = seed_demo(client, admin, db, data_dir)
    env = {
        "BASE_URL": f"http://host.docker.internal:{ui_server}",
        "DCP_API_KEY": admin["Authorization"].removeprefix("Bearer "),
        "DCP_PROJECT_ID": seeded["project_id"],
    }
    command = ["docker", "run", "--rm", "--add-host", "host.docker.internal:host-gateway"]
    for name, value in env.items():
        command += ["-e", f"{name}={value}"]
    command += [
        "-v",
        f"{ROOT / 'web'}:/web",
        "-w",
        "/web",
        PLAYWRIGHT_IMAGE,
        "npx",
        "playwright",
        "test",
        # e.g. DCP_PLAYWRIGHT_ARGS="e2e/u5-tutorial.spec.ts" to run one file while debugging
        *os.environ.get("DCP_PLAYWRIGHT_ARGS", "").split(),
    ]
    result = subprocess.run(  # noqa: S603 (fixed command, arguments chosen by the test)
        command, capture_output=True, text=True, timeout=600, env={**os.environ}
    )
    assert result.returncode == 0, result.stdout[-6000:] + result.stderr[-3000:]
    print(result.stdout[-3000:])  # the Playwright summary, shown with pytest -s
