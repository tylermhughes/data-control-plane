from fastapi import APIRouter

from app.api.deps import PrincipalDep, SessionDep
from app.api.problems import AUTH_ERRORS
from app.models import ApiKey as ApiKeyRow
from app.schemas.api_keys import ApiKey

router = APIRouter(tags=["api keys"])


@router.get("/me", summary="Which API key am I using?", responses=AUTH_ERRORS)
def me(session: SessionDep, principal: PrincipalDep) -> ApiKey:
    """Works with any valid key. Handy for checking that a key works and what it can do."""
    return ApiKey.model_validate(session.get_one(ApiKeyRow, principal.key_id or ""))
