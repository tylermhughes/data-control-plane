import os
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point the app at the throwaway test database before it is imported.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://dcp:dcp-test@127.0.0.1:55432/dcp_test"
)
os.environ.setdefault("DCP_SECRET_KEY", "test-only-secret-key-not-for-real-use-0123456789")
# Quality checks read local files from here (file:// URIs must be inside it).
DATA_DIR = Path(tempfile.mkdtemp(prefix="dcp-test-data-")).resolve()
os.environ["DCP_LOCAL_DATA_DIR"] = str(DATA_DIR)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.schemas.api_keys import ApiKeyCreate  # noqa: E402
from app.services import api_keys  # noqa: E402
from app.services.principal import CLI  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Rebuild the schema from scratch with the real migrations (tests downgrade and upgrade)."""
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def clean_tables() -> None:
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with get_engine().begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db() -> Iterator[Session]:
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


MakeKey = Callable[..., dict[str, str]]


@pytest.fixture
def make_key(db: Session) -> MakeKey:
    """Create a key directly in the database; returns Authorization headers for it."""

    def _make(
        role: str = "admin", access: str = "write", project_id: str | None = None
    ) -> dict[str, str]:
        _, secret = api_keys.create_key(
            db,
            CLI,
            ApiKeyCreate(name=f"{role}-{access}", role=role, access=access, project_id=project_id),  # type: ignore[arg-type]
        )
        db.commit()
        return {"Authorization": f"Bearer {secret}"}

    return _make


@pytest.fixture
def admin(make_key: MakeKey) -> dict[str, str]:
    return make_key()


@pytest.fixture
def data_dir() -> Path:
    return DATA_DIR
