from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.webhooks import (
    Event,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointCreate,
    WebhookEndpointCreated,
    WebhookEndpointUpdate,
    WebhookSecret,
)
from app.services import webhooks

endpoints = APIRouter(prefix="/webhook-endpoints", tags=["webhooks"])
deliveries = APIRouter(prefix="/webhook-deliveries", tags=["webhooks"])
events = APIRouter(prefix="/events", tags=["events"])


# --- endpoints -------------------------------------------------------------------------------


@endpoints.get("", summary="List webhook endpoints", responses=READ_ERRORS)
def list_endpoints(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[WebhookEndpoint]:
    rows, next_cursor = webhooks.list_endpoints(
        session, principal, project_id=project_id, limit=limit, cursor=cursor
    )
    return Page(data=[WebhookEndpoint.model_validate(r) for r in rows], next_cursor=next_cursor)


@endpoints.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WebhookEndpointCreated,
    summary="Register a webhook endpoint",
    responses=WRITE_ERRORS,
)
def create_endpoint(
    body: WebhookEndpointCreate,
    session: SessionDep,
    principal: PrincipalDep,
    idem: IdempotencyDep,
) -> WebhookEndpointCreated | Response:
    """DCP will POST a signed JSON message here for every matching event, following the
    [Standard Webhooks](https://www.standardwebhooks.com) format:

    - headers `webhook-id` (the event id), `webhook-timestamp` (Unix seconds) and
      `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">`, using `secret`)
    - body `{"id", "type", "timestamp", "project_id", "subject_id", "data"}`

    Failed deliveries are retried for about a day. Messages may arrive out of order; use
    `id` to skip duplicates and `timestamp` to order them."""
    if idem.replay:
        return idem.replay
    ep = webhooks.create_endpoint(session, principal, body)
    out = WebhookEndpoint.model_validate(ep)
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return WebhookEndpointCreated(**out.model_dump(), secret=webhooks.secret_of(ep).secret)


@endpoints.get("/{endpoint_id}", summary="Get a webhook endpoint", responses=READ_ERRORS)
def get_endpoint(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> WebhookEndpoint:
    return WebhookEndpoint.model_validate(webhooks.get_endpoint(session, principal, endpoint_id))


@endpoints.patch("/{endpoint_id}", summary="Update a webhook endpoint", responses=WRITE_ERRORS)
def update_endpoint(
    endpoint_id: str, body: WebhookEndpointUpdate, session: SessionDep, principal: PrincipalDep
) -> WebhookEndpoint:
    out = WebhookEndpoint.model_validate(
        webhooks.update_endpoint(session, principal, endpoint_id, body)
    )
    session.commit()
    return out


@endpoints.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a webhook endpoint",
    responses=WRITE_ERRORS,
)
def delete_endpoint(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Also deletes its delivery log. To stop deliveries for a while, set `enabled: false`."""
    webhooks.delete_endpoint(session, principal, endpoint_id)
    session.commit()


@endpoints.get("/{endpoint_id}/secret", summary="Show the signing secret", responses=WRITE_ERRORS)
def get_secret(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> WebhookSecret:
    """Needs write access."""
    return webhooks.get_secret(session, principal, endpoint_id)


@endpoints.post(
    "/{endpoint_id}/rotate-secret", summary="Rotate the signing secret", responses=WRITE_ERRORS
)
def rotate_secret(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> WebhookSecret:
    """Issues a new secret. For 24 hours, messages are signed with both the new and the
    previous secret, so the receiver can switch over without missing any."""
    out = webhooks.rotate_secret(session, principal, endpoint_id)
    session.commit()
    return out


@endpoints.post(
    "/{endpoint_id}/test",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send a test message",
    responses=WRITE_ERRORS,
)
def send_test(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> WebhookDelivery:
    """Queues a `webhook.test` message for this endpoint; the worker sends it within about a
    second. Check the result with `GET /v1/webhook-deliveries/{id}`."""
    out = WebhookDelivery.model_validate(webhooks.send_test(session, principal, endpoint_id))
    session.commit()
    return out


# --- deliveries ------------------------------------------------------------------------------


@deliveries.get("", summary="List webhook deliveries", responses=READ_ERRORS)
def list_deliveries(
    session: SessionDep,
    principal: PrincipalDep,
    endpoint_id: Annotated[str | None, Query(description="Only to this endpoint.")] = None,
    event_id: Annotated[str | None, Query(description="Only for this event.")] = None,
    status: Annotated[
        Literal["pending", "delivered", "failed"] | None, Query(description="Only this status.")
    ] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[WebhookDelivery]:
    rows, next_cursor = webhooks.list_deliveries(
        session,
        principal,
        endpoint_id=endpoint_id,
        event_id=event_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[WebhookDelivery.model_validate(r) for r in rows], next_cursor=next_cursor)


@deliveries.get("/{delivery_id}", summary="Get a delivery and its attempts", responses=READ_ERRORS)
def get_delivery(delivery_id: str, session: SessionDep, principal: PrincipalDep) -> WebhookDelivery:
    return WebhookDelivery.model_validate(webhooks.get_delivery(session, principal, delivery_id))


@deliveries.post(
    "/{delivery_id}/redeliver",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send a delivery again",
    responses=WRITE_ERRORS,
)
def redeliver(delivery_id: str, session: SessionDep, principal: PrincipalDep) -> WebhookDelivery:
    """Queues the same message again as a new delivery (same `webhook-id`, so receivers that
    skip duplicates will skip it). The original's log is kept."""
    out = WebhookDelivery.model_validate(webhooks.redeliver(session, principal, delivery_id))
    session.commit()
    return out


# --- event log -------------------------------------------------------------------------------


@events.get("", summary="List events", responses=READ_ERRORS)
def list_events(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    type: Annotated[
        str | None, Query(description="An event type (`batch.accepted`) or group (`batch.*`).")
    ] = None,
    subject_id: Annotated[str | None, Query(description="Only about this object.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Event]:
    """Every change recorded by DCP, oldest first. Project keys see their project's events."""
    rows, next_cursor = webhooks.list_events(
        session,
        principal,
        project_id=project_id,
        type=type,
        subject_id=subject_id,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[Event.model_validate(r) for r in rows], next_cursor=next_cursor)


@events.get("/{event_id}", summary="Get an event", responses=READ_ERRORS)
def get_event(event_id: str, session: SessionDep, principal: PrincipalDep) -> Event:
    return Event.model_validate(webhooks.get_event(session, principal, event_id))
