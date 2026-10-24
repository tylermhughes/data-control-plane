"""The API server. Run with: uvicorn app.main:app"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import log_filters
from app.api import health, problems, v1
from app.config import get_settings
from app.db import get_engine
from app.services import api_keys

logging.basicConfig(level=get_settings().log_level)
log_filters.install()
logger = logging.getLogger("app")


def operation_id(route: APIRoute) -> str:
    """Operation ids are the endpoint function names (list_batches), so generated clients
    get readable method names. They must be unique; a test checks that."""
    return route.name


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        with Session(get_engine()) as session:
            if not api_keys.has_active_admin_key(session):
                logger.warning(
                    "No admin API key exists yet. Create one with: "
                    "docker compose exec api python -m app.cli create-admin-key"
                )
    except SQLAlchemyError:
        logger.warning("Could not reach the database at startup.")
    yield


app = FastAPI(
    title="Data Control Plane API",
    version="0.9.0",
    description=(
        "The control plane for AI training data: plan, route, check and measure data "
        "from every source. Everything the product does is available through this API.\n\n"
        "**Authentication:** send your API key as `Authorization: Bearer dcp_...` "
        "(in these docs, use the **Authorize** button). "
        "**Errors** use the RFC 9457 problem format. "
        "**Retries:** POST requests accept an `Idempotency-Key` header."
    ),
    lifespan=lifespan,
    generate_unique_id_function=operation_id,
)
problems.install(app)
app.include_router(health.router)
app.include_router(v1.router)
