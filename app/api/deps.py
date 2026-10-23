"""Shared request dependencies: database session, caller identity, paging."""

from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_session
from app.errors import Unauthorized
from app.services import api_keys
from app.services.principal import Principal

_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="ApiKey",
    description="Your API key, e.g. `dcp_...`. Sent as `Authorization: Bearer dcp_...`.",
)

SessionDep = Annotated[Session, Depends(get_session)]


def get_principal(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if credentials is None:
        raise Unauthorized("Missing API key. Send 'Authorization: Bearer dcp_...'.")
    return api_keys.authenticate(session, credentials.credentials)


PrincipalDep = Annotated[Principal, Depends(get_principal)]
Limit = Annotated[int, Query(ge=1, le=200, description="Maximum items per page.")]
Cursor = Annotated[str | None, Query(description="`next_cursor` from the previous page.")]
ProjectFilter = Annotated[
    str | None,
    Query(description="Only items in this project. Project keys always see only theirs."),
]
