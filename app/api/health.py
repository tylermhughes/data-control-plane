"""Status checks used by Docker, load balancers and monitoring. Not versioned, no auth."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.health import Health, Readiness

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Is the server running?")
def healthz() -> Health:
    return Health(status="ok")


@router.get(
    "/readyz",
    summary="Can the server reach the database?",
    responses={503: {"model": Readiness, "description": "Database unreachable"}},
)
def readyz(response: Response, session: Annotated[Session, Depends(get_session)]) -> Readiness:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("readiness check: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return Readiness(status="unavailable", database="unavailable")
    return Readiness(status="ok", database="ok")
