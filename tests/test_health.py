from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import get_session
from app.main import app


def test_healthz_reports_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_database_ok(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_readyz_returns_503_when_database_is_down(client: TestClient) -> None:
    class BrokenSession:
        def execute(self, *_: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    def broken_session() -> Iterator[Session]:
        yield BrokenSession()  # type: ignore[misc]

    app.dependency_overrides[get_session] = broken_session
    try:
        response = client.get("/readyz")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


def test_api_docs_are_served(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Data Control Plane API"


def test_web_interface_is_served_without_taking_over_the_api(tmp_path: object) -> None:
    from pathlib import Path

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import problems, web

    root = Path(str(tmp_path))
    (root / "assets").mkdir()
    (root / "index.html").write_text("<div id=root></div>")
    (root / "assets" / "app.js").write_text("console.log(1)")
    (root / "favicon.svg").write_text("<svg/>")
    ui = FastAPI()
    problems.install(ui)
    assert web.install(ui, str(root))
    client = TestClient(ui)

    page = client.get("/portfolio")  # a UI route: served by index.html
    assert page.status_code == 200 and "root" in page.text
    assert page.headers["cache-control"] == "no-cache"
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/favicon.svg").text == "<svg/>"
    missing_api = client.get("/v1/nothing-here")
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"] == "application/problem+json"
    assert client.get("/../../etc/passwd").text == "<div id=root></div>"  # never outside the UI


def test_no_web_interface_when_not_built(tmp_path: object) -> None:
    from fastapi import FastAPI

    from app.api import web

    assert web.install(FastAPI(), str(tmp_path)) is False
