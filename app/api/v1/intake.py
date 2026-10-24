from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status
from starlette.concurrency import run_in_threadpool

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS, problem_responses
from app.schemas.common import Page
from app.schemas.intake import (
    Connector,
    ConnectorCreate,
    ConnectorObject,
    ConnectorUpdate,
    InboundEndpoint,
    InboundEndpointCreate,
    InboundEndpointCreated,
    InboundEndpointUpdate,
    InboundMessageLog,
    InboundResult,
    PollResult,
)
from app.schemas.webhooks import WebhookSecret
from app.services import connectors, inbound

DataSourceFilter = Annotated[str | None, Query(description="Only for this data source.")]

inbound_endpoints = APIRouter(prefix="/inbound-webhooks", tags=["intake"])
inbound_receiver = APIRouter(prefix="/inbound", tags=["intake"])
connector_routes = APIRouter(prefix="/connectors", tags=["intake"])


# --- inbound webhook endpoints ---------------------------------------------------------------


@inbound_endpoints.get("", summary="List inbound webhooks", responses=READ_ERRORS)
def list_inbound(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    data_source_id: DataSourceFilter = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[InboundEndpoint]:
    rows, next_cursor = inbound.list_endpoints(
        session,
        principal,
        project_id=project_id,
        data_source_id=data_source_id,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[InboundEndpoint.model_validate(r) for r in rows], next_cursor=next_cursor)


@inbound_endpoints.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=InboundEndpointCreated,
    summary="Create an inbound webhook",
    responses=WRITE_ERRORS,
)
def create_inbound(
    body: InboundEndpointCreate,
    session: SessionDep,
    principal: PrincipalDep,
    idem: IdempotencyDep,
) -> InboundEndpointCreated | Response:
    """Gives a data source's own systems a URL to push deliveries to. Give the sender the
    `url_path` (on DCP's address) and the `secret`; they sign each message with it using
    [Standard Webhooks](https://www.standardwebhooks.com), the same way DCP signs its outbound
    webhooks. See `POST /v1/inbound/{id}` for the message format."""
    if idem.replay:
        return idem.replay
    ep = inbound.create_endpoint(session, principal, body)
    out = InboundEndpoint.model_validate(ep)
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return InboundEndpointCreated(**out.model_dump(), secret=inbound.secret_for(ep))


@inbound_endpoints.get("/{endpoint_id}", summary="Get an inbound webhook", responses=READ_ERRORS)
def get_inbound(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> InboundEndpoint:
    return InboundEndpoint.model_validate(inbound.get_endpoint(session, principal, endpoint_id))


@inbound_endpoints.patch(
    "/{endpoint_id}", summary="Update an inbound webhook", responses=WRITE_ERRORS
)
def update_inbound(
    endpoint_id: str, body: InboundEndpointUpdate, session: SessionDep, principal: PrincipalDep
) -> InboundEndpoint:
    out = InboundEndpoint.model_validate(
        inbound.update_endpoint(session, principal, endpoint_id, body)
    )
    session.commit()
    return out


@inbound_endpoints.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an inbound webhook",
    responses=WRITE_ERRORS,
)
def delete_inbound(endpoint_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Batches it created stay; its message log goes."""
    inbound.delete_endpoint(session, principal, endpoint_id)
    session.commit()


@inbound_endpoints.get(
    "/{endpoint_id}/secret", summary="Show the signing secret", responses=WRITE_ERRORS
)
def get_inbound_secret(
    endpoint_id: str, session: SessionDep, principal: PrincipalDep
) -> WebhookSecret:
    """Needs write access."""
    return WebhookSecret(
        secret=inbound.get_secret(session, principal, endpoint_id),
        previous_secret_valid_until=None,
    )


@inbound_endpoints.post(
    "/{endpoint_id}/rotate-secret", summary="Rotate the signing secret", responses=WRITE_ERRORS
)
def rotate_inbound_secret(
    endpoint_id: str, session: SessionDep, principal: PrincipalDep
) -> WebhookSecret:
    """Issues a new secret. Messages signed with the previous one are still accepted for 24
    hours, so the sender can switch over."""
    secret = inbound.rotate_secret(session, principal, endpoint_id)
    ep = inbound.get_endpoint(session, principal, endpoint_id)
    session.commit()
    until = ep.secret_rotated_at + timedelta(hours=24) if ep.secret_rotated_at else None
    return WebhookSecret(secret=secret, previous_secret_valid_until=until)


@inbound_endpoints.get(
    "/{endpoint_id}/messages", summary="Messages received", responses=READ_ERRORS
)
def list_inbound_messages(
    endpoint_id: str,
    session: SessionDep,
    principal: PrincipalDep,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[InboundMessageLog]:
    """Every message, processed or rejected, with the reason it was rejected."""
    rows, next_cursor = inbound.list_messages(
        session, principal, endpoint_id, limit=limit, cursor=cursor
    )
    return Page(data=[InboundMessageLog.model_validate(r) for r in rows], next_cursor=next_cursor)


# --- receiving (no API key: the signature is the authentication) ----------------------------


@inbound_receiver.post(
    "/{endpoint_id}",
    summary="Receive a signed delivery message",
    responses=problem_responses(401, 403, 404, 409, 422),
)
async def receive(endpoint_id: str, request: Request, session: SessionDep) -> InboundResult:
    """Called by the source's systems, not with an API key. Headers (Standard Webhooks):
    `webhook-id` (unique per message), `webhook-timestamp` (Unix seconds, within 5 minutes),
    `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">` with the secret).

    Body: `{"type": "batch.delivered", "data": {...}}`, where `data` has the fields of
    `POST /v1/batches`. `allocation_id` may be left out if the source has exactly one active
    allocation. Sending the same `webhook-id` again returns the first result
    (`duplicate: true`); a new message with the same `external_ref` updates the batch."""
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    # The database work runs in a worker thread, so a slow message can't stall the server.
    return await run_in_threadpool(inbound.receive, session, endpoint_id, headers, body)


# --- connectors ------------------------------------------------------------------------------


@connector_routes.get("", summary="List connectors", responses=READ_ERRORS)
def list_connectors(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    data_source_id: DataSourceFilter = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Connector]:
    rows, next_cursor = connectors.list_connectors(
        session,
        principal,
        project_id=project_id,
        data_source_id=data_source_id,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[Connector.model_validate(r) for r in rows], next_cursor=next_cursor)


@connector_routes.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Connector,
    summary="Watch a bucket for deliveries",
    responses=WRITE_ERRORS,
)
def create_connector(
    body: ConnectorCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Connector | Response:
    """DCP checks the bucket folder about every `poll_interval_seconds` and turns each new
    file (.jsonl, .ndjson, .csv, .parquet) into a batch of the data source. Its quality checks
    then run automatically; `delivered_count` comes from the files and `spend` is estimated
    from the allocation's quoted rate until someone sets it. Files whose names start with `.`
    or `_` are ignored. Credentials are stored encrypted and never shown again."""
    if idem.replay:
        return idem.replay
    out = Connector.model_validate(connectors.create_connector(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@connector_routes.get("/{connector_id}", summary="Get a connector", responses=READ_ERRORS)
def get_connector(connector_id: str, session: SessionDep, principal: PrincipalDep) -> Connector:
    return Connector.model_validate(connectors.get_connector(session, principal, connector_id))


@connector_routes.patch("/{connector_id}", summary="Update a connector", responses=WRITE_ERRORS)
def update_connector(
    connector_id: str, body: ConnectorUpdate, session: SessionDep, principal: PrincipalDep
) -> Connector:
    out = Connector.model_validate(
        connectors.update_connector(session, principal, connector_id, body)
    )
    session.commit()
    return out


@connector_routes.delete(
    "/{connector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a connector",
    responses=WRITE_ERRORS,
)
def delete_connector(connector_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Batches it created stay."""
    connectors.delete_connector(session, principal, connector_id)
    session.commit()


@connector_routes.post(
    "/{connector_id}/poll", summary="Check the bucket now", responses=WRITE_ERRORS
)
def poll_now(connector_id: str, session: SessionDep, principal: PrincipalDep) -> PollResult:
    """Lists the bucket right away instead of waiting for the next scheduled check."""
    return connectors.poll_now(session, principal, connector_id)


@connector_routes.get(
    "/{connector_id}/objects", summary="Files the connector has seen", responses=READ_ERRORS
)
def list_objects(
    connector_id: str,
    session: SessionDep,
    principal: PrincipalDep,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[ConnectorObject]:
    rows, next_cursor = connectors.list_objects(
        session, principal, connector_id, limit=limit, cursor=cursor
    )
    return Page(data=[ConnectorObject.model_validate(r) for r in rows], next_cursor=next_cursor)
