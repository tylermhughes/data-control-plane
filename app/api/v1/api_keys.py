from fastapi import APIRouter, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.api_keys import ApiKey, ApiKeyCreate, ApiKeyCreated, ApiKeyUpdate
from app.schemas.common import Page
from app.services import api_keys

router = APIRouter(prefix="/api-keys", tags=["api keys"])


@router.get("", summary="List API keys", responses=READ_ERRORS)
def list_keys(
    session: SessionDep, principal: PrincipalDep, limit: Limit = 50, cursor: Cursor = None
) -> Page[ApiKey]:
    """Needs an admin key. Includes revoked keys (see `revoked_at`). Secrets are never shown."""
    rows, next_cursor = api_keys.list_keys(session, principal, limit=limit, cursor=cursor)
    return Page(data=[ApiKey.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiKeyCreated,
    summary="Create an API key",
    responses=WRITE_ERRORS,
)
def create_key(
    body: ApiKeyCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> ApiKeyCreated | Response:
    """Needs an admin key with write access. The response includes `secret`, the full key.
    It is shown only this once.

    A retry with the same Idempotency-Key does **not** show the secret again; create a new key
    if it was lost.
    """
    if idem.replay:
        return idem.replay
    key, secret = api_keys.create_key(session, principal, body)
    out = ApiKey.model_validate(key)
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return ApiKeyCreated(**out.model_dump(), secret=secret)


@router.get("/{key_id}", summary="Get an API key", responses=READ_ERRORS)
def get_key(key_id: str, session: SessionDep, principal: PrincipalDep) -> ApiKey:
    return ApiKey.model_validate(api_keys.get_key(session, principal, key_id))


@router.patch("/{key_id}", summary="Rename an API key", responses=WRITE_ERRORS)
def rename_key(
    key_id: str, body: ApiKeyUpdate, session: SessionDep, principal: PrincipalDep
) -> ApiKey:
    out = ApiKey.model_validate(api_keys.rename_key(session, principal, key_id, body))
    session.commit()
    return out


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
    responses=WRITE_ERRORS,
)
def revoke_key(key_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """The key stops working immediately. Revoking an already-revoked key does nothing.
    The last active admin key with write access cannot be revoked."""
    api_keys.revoke_key(session, principal, key_id)
    session.commit()
