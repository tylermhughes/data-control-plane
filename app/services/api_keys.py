import hashlib
import secrets
from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid, NotFound, Unauthorized
from app.ids import new_id
from app.models import ApiKey, Project
from app.models.base import utcnow
from app.schemas import api_keys as schemas
from app.services import events
from app.services.pagination import paginate
from app.services.principal import Principal

KEY_PREFIX = "dcp_"
_LAST_USED_RESOLUTION = timedelta(minutes=1)


def hash_secret(secret: str) -> str:
    # Keys are 256 random bits, so a plain SHA-256 is safe here (no slow hash needed).
    return hashlib.sha256(secret.encode()).hexdigest()


def _emit(session: Session, type: str, key: ApiKey, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.ApiKey.model_validate(key),
        subject_id=key.id,
        project_id=key.project_id,
        actor=actor,
    )


def authenticate(session: Session, secret: str) -> Principal:
    if not secret.startswith(KEY_PREFIX):
        raise Unauthorized("Invalid API key. Keys start with 'dcp_'.")
    key = session.scalar(select(ApiKey).where(ApiKey.key_hash == hash_secret(secret)))
    if key is None or key.revoked_at is not None:
        raise Unauthorized("Invalid or revoked API key.")
    now = utcnow()
    if key.last_used_at is None or now - key.last_used_at > _LAST_USED_RESOLUTION:
        key.last_used_at = now
        session.commit()
    return Principal(key_id=key.id, role=key.role, access=key.access, project_id=key.project_id)


def list_keys(
    session: Session, actor: Principal, *, limit: int, cursor: str | None
) -> tuple[Sequence[ApiKey], str | None]:
    actor.require_admin()
    return paginate(session, select(ApiKey), ApiKey.id, limit=limit, cursor=cursor)


def get_key(session: Session, actor: Principal, key_id: str) -> ApiKey:
    actor.require_admin()
    key = session.get(ApiKey, key_id)
    if key is None:
        raise NotFound(f"No API key with id '{key_id}'.")
    return key


def create_key(
    session: Session, actor: Principal, body: schemas.ApiKeyCreate
) -> tuple[ApiKey, str]:
    """Create a key. Returns the key row and the secret, which is never stored."""
    actor.require_admin()
    actor.require_write()
    if body.project_id and session.get(Project, body.project_id) is None:
        raise Invalid(f"No project with id '{body.project_id}'.")
    secret = KEY_PREFIX + secrets.token_urlsafe(32)
    key = ApiKey(
        id=new_id("key"),
        name=body.name,
        key_prefix=secret[:12],
        key_hash=hash_secret(secret),
        role=body.role,
        access=body.access,
        project_id=body.project_id,
    )
    session.add(key)
    session.flush()
    _emit(session, "api_key.created", key, actor)
    return key, secret


def rename_key(
    session: Session, actor: Principal, key_id: str, body: schemas.ApiKeyUpdate
) -> ApiKey:
    key = get_key(session, actor, key_id)
    actor.require_write()
    key.name = body.name
    session.flush()
    _emit(session, "api_key.updated", key, actor)
    return key


def revoke_key(session: Session, actor: Principal, key_id: str) -> None:
    key = get_key(session, actor, key_id)
    actor.require_write()
    if key.revoked_at is not None:
        return
    if key.role == "admin" and key.access == "write" and _active_admin_writers(session) <= 1:
        raise Conflict(
            "This is the last active admin key with write access. "
            "Create another admin key before revoking this one."
        )
    key.revoked_at = utcnow()
    session.flush()
    _emit(session, "api_key.revoked", key, actor)


def _active_admin_writers(session: Session) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(ApiKey)
            .where(ApiKey.role == "admin", ApiKey.access == "write", ApiKey.revoked_at.is_(None))
        )
        or 0
    )


def has_active_admin_key(session: Session) -> bool:
    return _active_admin_writers(session) > 0
