import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# Point the app at the throwaway test database before it is imported.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://dcp:dcp-test@127.0.0.1:55432/dcp_test"
)

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
