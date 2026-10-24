from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.webhook_endpoint_create import WebhookEndpointCreate
from ...models.webhook_endpoint_created import WebhookEndpointCreated
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: WebhookEndpointCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["idempotency-key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/webhook-endpoints",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | WebhookEndpointCreated | None:
    if response.status_code == 201:
        response_201 = WebhookEndpointCreated.from_dict(response.json())

        return response_201

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 409:
        response_409 = cast(Any, None)
        return response_409

    if response.status_code == 422:
        response_422 = cast(Any, None)
        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | WebhookEndpointCreated]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: WebhookEndpointCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | WebhookEndpointCreated]:
    """Register a webhook endpoint

     DCP will POST a signed JSON message here for every matching event, following the
    [Standard Webhooks](https://www.standardwebhooks.com) format:

    - headers `webhook-id` (the event id), `webhook-timestamp` (Unix seconds) and
      `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">`, using `secret`)
    - body `{"id", "type", "timestamp", "project_id", "subject_id", "data"}`

    Failed deliveries are retried for about a day. Messages may arrive out of order; use
    `id` to skip duplicates and `timestamp` to order them.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (WebhookEndpointCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WebhookEndpointCreated]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: WebhookEndpointCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | WebhookEndpointCreated | None:
    """Register a webhook endpoint

     DCP will POST a signed JSON message here for every matching event, following the
    [Standard Webhooks](https://www.standardwebhooks.com) format:

    - headers `webhook-id` (the event id), `webhook-timestamp` (Unix seconds) and
      `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">`, using `secret`)
    - body `{"id", "type", "timestamp", "project_id", "subject_id", "data"}`

    Failed deliveries are retried for about a day. Messages may arrive out of order; use
    `id` to skip duplicates and `timestamp` to order them.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (WebhookEndpointCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WebhookEndpointCreated
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: WebhookEndpointCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | WebhookEndpointCreated]:
    """Register a webhook endpoint

     DCP will POST a signed JSON message here for every matching event, following the
    [Standard Webhooks](https://www.standardwebhooks.com) format:

    - headers `webhook-id` (the event id), `webhook-timestamp` (Unix seconds) and
      `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">`, using `secret`)
    - body `{"id", "type", "timestamp", "project_id", "subject_id", "data"}`

    Failed deliveries are retried for about a day. Messages may arrive out of order; use
    `id` to skip duplicates and `timestamp` to order them.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (WebhookEndpointCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WebhookEndpointCreated]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: WebhookEndpointCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | WebhookEndpointCreated | None:
    """Register a webhook endpoint

     DCP will POST a signed JSON message here for every matching event, following the
    [Standard Webhooks](https://www.standardwebhooks.com) format:

    - headers `webhook-id` (the event id), `webhook-timestamp` (Unix seconds) and
      `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">`, using `secret`)
    - body `{"id", "type", "timestamp", "project_id", "subject_id", "data"}`

    Failed deliveries are retried for about a day. Messages may arrive out of order; use
    `id` to skip duplicates and `timestamp` to order them.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (WebhookEndpointCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WebhookEndpointCreated
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
