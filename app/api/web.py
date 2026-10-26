"""Serves the web interface (web/dist, built into the Docker image) next to the API.

API paths (/v1, /docs, /openapi.json, health checks) are never taken over: an unknown /v1
path is still a 404 problem response. Every other path serves the UI's files, or its
index.html so the UI's own router can show the right page.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.errors import NotFound

API_PATHS = ("v1", "docs", "redoc", "openapi.json", "healthz", "readyz")


def install(app: FastAPI, web_dir: str) -> bool:
    """Serve the UI if it has been built into `web_dir`. Returns whether it is served."""
    root = Path(web_dir).resolve()
    index = root / "index.html"
    if not index.is_file():
        return False
    if (root / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=root / "assets"), name="web-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str) -> FileResponse:
        first = path.split("/", 1)[0]
        if first in API_PATHS:
            raise NotFound(f"No such API path: /{path}")
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        # index.html must never be cached, so a new release is picked up straight away.
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return True
