"""Webhook endpoints, deliveries and the event log, as seen through the API.

Endpoints belong to one project (they get that project's events) or, for admin keys, to no
project (org-wide: every project's events). The worker side lives in app.services.dispatch.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.errors import Invalid, NotFound
from app.ids import new_id
from app.models import Event, Project, WebhookDelivery, WebhookEndpoint
from app.models.base import utcnow
from app.schemas import webhooks as schemas
from app.services import events, scoped, signing
from app.services.pagination import paginate
from app.services.principal import Principal

ROTATION_OVERLAP = timedelta(hours=24)


def _emit(session: Session, type: str, ep: WebhookEndpoint, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.WebhookEndpoint.model_validate(ep),
        subject_id=ep.id,
        project_id=ep.project_id,
        actor=actor,
    )


def _can_see(actor: Principal, project_id: str | None) -> bool:
    return actor.is_admin if project_id is None else actor.can_see_project(project_id)


# --- endpoints -------------------------------------------------------------------------------


def list_endpoints(
    session: Session, actor: Principal, *, project_id: str | None, limit: int, cursor: str | None
) -> tuple[Sequence[WebhookEndpoint], str | None]:
    stmt = select(WebhookEndpoint)
    if not actor.is_admin:
        stmt = stmt.where(WebhookEndpoint.project_id == actor.project_id)
    if project_id:
        stmt = stmt.where(WebhookEndpoint.project_id == project_id)
    return paginate(session, stmt, WebhookEndpoint.id, limit=limit, cursor=cursor)


def get_endpoint(session: Session, actor: Principal, endpoint_id: str) -> WebhookEndpoint:
    ep = session.get(WebhookEndpoint, endpoint_id)
    if ep is None or not _can_see(actor, ep.project_id):
        raise NotFound(f"No webhook endpoint with id '{endpoint_id}'.")
    return ep


def create_endpoint(
    session: Session, actor: Principal, body: schemas.WebhookEndpointCreate
) -> WebhookEndpoint:
    actor.require_write()
    project_id = body.project_id or actor.project_id  # admins without one: org-wide
    if project_id is not None and (
        not actor.can_see_project(project_id) or session.get(Project, project_id) is None
    ):
        raise Invalid(f"No project with id '{project_id}'.")
    ep = WebhookEndpoint(
        id=new_id("whk"),
        project_id=project_id,
        url=body.url,
        description=body.description,
        event_types=body.event_types,
        enabled=body.enabled,
        secret_version=1,
    )
    session.add(ep)
    session.flush()
    _emit(session, "webhook_endpoint.created", ep, actor)
    return ep


def update_endpoint(
    session: Session, actor: Principal, endpoint_id: str, body: schemas.WebhookEndpointUpdate
) -> WebhookEndpoint:
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    scoped.apply_changes(ep, body.model_dump(exclude_unset=True, exclude_none=True))
    session.flush()
    _emit(session, "webhook_endpoint.updated", ep, actor)
    return ep


def delete_endpoint(session: Session, actor: Principal, endpoint_id: str) -> None:
    """Also deletes its delivery log."""
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    _emit(session, "webhook_endpoint.deleted", ep, actor)
    session.delete(ep)
    session.flush()


def secret_of(ep: WebhookEndpoint, now: datetime | None = None) -> schemas.WebhookSecret:
    valid_until = None
    if ep.secret_rotated_at and ep.secret_version > 1:
        until = ep.secret_rotated_at + ROTATION_OVERLAP
        if until > (now or utcnow()):
            valid_until = until
    return schemas.WebhookSecret(
        secret=signing.display_secret(ep.id, ep.secret_version),
        previous_secret_valid_until=valid_until,
    )


def get_secret(session: Session, actor: Principal, endpoint_id: str) -> schemas.WebhookSecret:
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()  # read-only keys can see endpoints but not their secrets
    return secret_of(ep)


def rotate_secret(session: Session, actor: Principal, endpoint_id: str) -> schemas.WebhookSecret:
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    ep.secret_version += 1
    ep.secret_rotated_at = utcnow()
    session.flush()
    _emit(session, "webhook_endpoint.secret_rotated", ep, actor)
    return secret_of(ep)


def send_test(session: Session, actor: Principal, endpoint_id: str) -> WebhookDelivery:
    """Queue a `webhook.test` message for this endpoint only (no event is recorded)."""
    ep = get_endpoint(session, actor, endpoint_id)
    actor.require_write()
    event_id = new_id("evt")
    now = utcnow()
    delivery = WebhookDelivery(
        id=new_id("dlv"),
        endpoint_id=ep.id,
        project_id=ep.project_id,
        event_id=event_id,
        event_type="webhook.test",
        payload={
            "id": event_id,
            "type": "webhook.test",
            "timestamp": now.isoformat(),
            "project_id": ep.project_id,
            "subject_id": ep.id,
            "data": {"message": "Test message from Data Control Plane.", "endpoint_id": ep.id},
        },
        next_attempt_at=now,
    )
    session.add(delivery)
    session.flush()
    return delivery


# --- deliveries ------------------------------------------------------------------------------


def _visible_deliveries(actor: Principal) -> list[ColumnElement[bool]]:
    if actor.is_admin:
        return []
    own = select(WebhookEndpoint.id).where(WebhookEndpoint.project_id == actor.project_id)
    return [WebhookDelivery.endpoint_id.in_(own)]


def list_deliveries(
    session: Session,
    actor: Principal,
    *,
    endpoint_id: str | None,
    event_id: str | None,
    status: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[WebhookDelivery], str | None]:
    stmt = select(WebhookDelivery).where(*_visible_deliveries(actor))
    if endpoint_id:
        stmt = stmt.where(WebhookDelivery.endpoint_id == endpoint_id)
    if event_id:
        stmt = stmt.where(WebhookDelivery.event_id == event_id)
    if status:
        stmt = stmt.where(WebhookDelivery.status == status)
    return paginate(session, stmt, WebhookDelivery.id, limit=limit, cursor=cursor)


def get_delivery(session: Session, actor: Principal, delivery_id: str) -> WebhookDelivery:
    delivery = session.get(WebhookDelivery, delivery_id)
    if delivery is None or not _can_see(actor, delivery.endpoint.project_id):
        raise NotFound(f"No webhook delivery with id '{delivery_id}'.")
    return delivery


def redeliver(session: Session, actor: Principal, delivery_id: str) -> WebhookDelivery:
    """Send the same message again, as a new delivery (the original's log is kept)."""
    original = get_delivery(session, actor, delivery_id)
    actor.require_write()
    copy = WebhookDelivery(
        id=new_id("dlv"),
        endpoint_id=original.endpoint_id,
        project_id=original.project_id,
        event_id=original.event_id,
        event_type=original.event_type,
        payload=original.payload,
        next_attempt_at=utcnow(),
        redelivery_of=original.id,
    )
    session.add(copy)
    session.flush()
    return copy


# --- event log -------------------------------------------------------------------------------


def list_events(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    type: str | None,
    subject_id: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Event], str | None]:
    stmt = select(Event)
    if not actor.is_admin:
        stmt = stmt.where(Event.project_id == actor.project_id)
    if project_id:
        stmt = stmt.where(Event.project_id == project_id)
    if type:
        if type.endswith(".*"):
            stmt = stmt.where(Event.type.startswith(type[:-1]))
        else:
            stmt = stmt.where(Event.type == type)
    if subject_id:
        stmt = stmt.where(Event.subject_id == subject_id)
    return paginate(session, stmt, Event.id, limit=limit, cursor=cursor)


def get_event(session: Session, actor: Principal, event_id: str) -> Event:
    event = session.get(Event, event_id)
    if event is None or not _can_see(actor, event.project_id):
        raise NotFound(f"No event with id '{event_id}'.")
    return event
