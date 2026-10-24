"""Inbound webhooks: a source's own systems push signed delivery messages to DCP.

The sender signs each message with the endpoint's secret, exactly like DCP's outbound
webhooks (Standard Webhooks). DCP refuses messages that are unsigned, wrongly signed, more than
5 minutes old or from the future, and answers a repeated message id with the original result
instead of processing it twice. Every message is logged, processed or rejected.

Body: {"type": "batch.delivered", "data": {...}} where data has the fields of POST /v1/batches.
`allocation_id` may be left out when the source has exactly one active allocation.
"""

import json
import time
from collections.abc import Sequence

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import DcpError, Forbidden, Invalid, NotFound, Unauthorized
from app.ids import new_id
from app.models import Allocation, DataSource, InboundEndpoint, InboundMessage
from app.models.base import utcnow
from app.schemas import batches as batch_schemas
from app.schemas import intake as schemas
from app.services import allocations, batches, events, scoped, signing
from app.services.principal import Principal

TOLERANCE_SECONDS = 5 * 60
MAX_BODY_BYTES = 1_000_000
MESSAGE_TYPES = ("batch.delivered",)


def secret_for(endpoint: InboundEndpoint, version: int | None = None) -> str:
    # A different derivation label from outbound secrets, so the two can never coincide.
    return signing.display_secret(f"inbound:{endpoint.id}", version or endpoint.secret_version)


def _emit(session: Session, type: str, ep: InboundEndpoint, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.InboundEndpoint.model_validate(ep),
        subject_id=ep.id,
        project_id=ep.project_id,
        actor=actor,
    )


# --- endpoints -------------------------------------------------------------------------------


def list_endpoints(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    data_source_id: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[InboundEndpoint], str | None]:
    where = [InboundEndpoint.data_source_id == data_source_id] if data_source_id else []
    return scoped.list_scoped(
        session,
        actor,
        InboundEndpoint,
        project_id=project_id,
        limit=limit,
        cursor=cursor,
        where=where,
    )


def get_endpoint(session: Session, actor: Principal, endpoint_id: str) -> InboundEndpoint:
    return scoped.get_scoped(session, actor, InboundEndpoint, endpoint_id, "inbound webhook")


def create_endpoint(
    session: Session, actor: Principal, body: schemas.InboundEndpointCreate
) -> InboundEndpoint:
    actor.require_write()
    source = session.get(DataSource, body.data_source_id)
    if source is None or not actor.can_see_project(source.project_id):
        raise Invalid(f"No data source with id '{body.data_source_id}'.")
    ep = InboundEndpoint(
        id=new_id("ihk"),
        project_id=source.project_id,
        data_source_id=source.id,
        description=body.description,
        enabled=body.enabled,
        secret_version=1,
    )
    session.add(ep)
    session.flush()
    _emit(session, "inbound_webhook.created", ep, actor)
    return ep


def update_endpoint(
    session: Session, actor: Principal, endpoint_id: str, body: schemas.InboundEndpointUpdate
) -> InboundEndpoint:
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    scoped.apply_changes(ep, body.model_dump(exclude_unset=True, exclude_none=True))
    session.flush()
    _emit(session, "inbound_webhook.updated", ep, actor)
    return ep


def delete_endpoint(session: Session, actor: Principal, endpoint_id: str) -> None:
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    _emit(session, "inbound_webhook.deleted", ep, actor)
    session.delete(ep)
    session.flush()


def get_secret(session: Session, actor: Principal, endpoint_id: str) -> str:
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    return secret_for(ep)


def rotate_secret(session: Session, actor: Principal, endpoint_id: str) -> str:
    """Issues a new secret. The previous one keeps working for 24 hours."""
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    ep.secret_version += 1
    ep.secret_rotated_at = utcnow()
    session.flush()
    _emit(session, "inbound_webhook.secret_rotated", ep, actor)
    return secret_for(ep)


def list_messages(
    session: Session, actor: Principal, endpoint_id: str, *, limit: int, cursor: str | None
) -> tuple[Sequence[InboundMessage], str | None]:
    from app.services.pagination import paginate

    get_endpoint(session, actor, endpoint_id)
    stmt = select(InboundMessage).where(InboundMessage.endpoint_id == endpoint_id)
    return paginate(session, stmt, InboundMessage.id, limit=limit, cursor=cursor)


# --- receiving -------------------------------------------------------------------------------


def _valid_secrets(ep: InboundEndpoint) -> list[str]:
    secrets = [secret_for(ep)]
    rotated = ep.secret_rotated_at
    if rotated and ep.secret_version > 1 and (utcnow() - rotated).total_seconds() < 86_400:
        secrets.append(secret_for(ep, ep.secret_version - 1))
    return secrets


def _log(
    session: Session,
    ep: InboundEndpoint,
    *,
    message_id: str | None,
    status: str,
    http_status: int,
    error: str | None = None,
    batch_id: str | None = None,
    message_type: str | None = None,
) -> None:
    session.add(
        InboundMessage(
            id=new_id("inm"),
            endpoint_id=ep.id,
            message_id=message_id,
            status=status,
            http_status=http_status,
            error=error,
            batch_id=batch_id,
            message_type=message_type,
        )
    )


def receive(
    session: Session, endpoint_id: str, headers: dict[str, str], body: bytes
) -> schemas.InboundResult:
    """Verify and process one message. Raises DcpError (logged) if it's refused."""
    ep = session.get(InboundEndpoint, endpoint_id)
    if ep is None:
        raise NotFound(f"No inbound webhook with id '{endpoint_id}'.")
    message_id = headers.get("webhook-id") or None
    try:
        return _process(session, ep, message_id, headers, body)
    except DcpError as exc:
        session.rollback()
        ep = session.get_one(InboundEndpoint, endpoint_id)
        _log(
            session,
            ep,
            message_id=message_id,
            status="rejected",
            http_status=exc.status,
            error=exc.detail,
        )
        session.commit()
        raise


def _process(
    session: Session,
    ep: InboundEndpoint,
    message_id: str | None,
    headers: dict[str, str],
    body: bytes,
) -> schemas.InboundResult:
    if not ep.enabled:
        raise Forbidden("This inbound webhook is disabled.")
    if len(body) > MAX_BODY_BYTES:
        raise Invalid("Message is larger than 1 MB.")
    timestamp, signature = (
        headers.get("webhook-timestamp", ""),
        headers.get("webhook-signature", ""),
    )
    if not message_id or not timestamp.isdigit() or not signature:
        raise Unauthorized("Missing webhook-id, webhook-timestamp or webhook-signature header.")
    if abs(time.time() - int(timestamp)) > TOLERANCE_SECONDS:
        raise Unauthorized("webhook-timestamp is more than 5 minutes away from now.")
    if not any(
        signing.verify(secret, message_id, int(timestamp), body, signature)
        for secret in _valid_secrets(ep)
    ):
        raise Unauthorized("Signature doesn't match.")

    earlier = session.scalar(
        select(InboundMessage).where(
            InboundMessage.endpoint_id == ep.id,
            InboundMessage.message_id == message_id,
            InboundMessage.status == "processed",
        )
    )
    if earlier is not None and earlier.batch_id:
        batch = batches.get_batch(session, _actor(ep), earlier.batch_id)
        return schemas.InboundResult(
            message_id=message_id,
            status="processed",
            batch_id=batch.id,
            batch_status=batch.status,
            duplicate=True,
        )

    try:
        message = json.loads(body)
        message_type, data = message["type"], message["data"]
    except (ValueError, KeyError, TypeError):
        raise Invalid(
            'Body must be JSON like {"type": "batch.delivered", "data": {...}}.'
        ) from None
    if message_type not in MESSAGE_TYPES:
        raise Invalid(f"Unknown message type '{message_type}'. Known: {', '.join(MESSAGE_TYPES)}.")
    if not isinstance(data, dict):
        raise Invalid("`data` must be an object.")

    data = {
        **data,
        "allocation_id": data.get("allocation_id")
        or allocations.single_active(session, ep.data_source_id),
    }
    try:
        create = batch_schemas.BatchCreate.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
        raise Invalid(f"Invalid delivery: {problems}") from None
    alloc = session.get(Allocation, create.allocation_id)
    if alloc is None or alloc.data_source_id != ep.data_source_id:
        raise Invalid("allocation_id must be an allocation of this webhook's data source.")

    batch, _ = batches.create_batch(session, _actor(ep), create)
    ep.last_received_at = utcnow()
    _log(
        session,
        ep,
        message_id=message_id,
        status="processed",
        http_status=200,
        batch_id=batch.id,
        message_type=message_type,
    )
    session.commit()
    return schemas.InboundResult(
        message_id=message_id,
        status="processed",
        batch_id=batch.id,
        batch_status=batch.status,
        duplicate=False,
    )


def _actor(ep: InboundEndpoint) -> Principal:
    """Messages act with write access to the endpoint's project only."""
    return Principal(key_id=None, role="project", access="write", project_id=ep.project_id)
