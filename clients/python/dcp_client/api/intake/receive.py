from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.inbound_result import InboundResult
from ...types import Response


def _get_kwargs(
    endpoint_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/inbound/{endpoint_id}".format(
            endpoint_id=quote(str(endpoint_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | InboundResult | None:
    if response.status_code == 200:
        response_200 = InboundResult.from_dict(response.json())

        return response_200

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | InboundResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | InboundResult]:
    """Receive a signed delivery message

     Called by the source's systems, not with an API key. Headers (Standard Webhooks):
    `webhook-id` (unique per message), `webhook-timestamp` (Unix seconds, within 5 minutes),
    `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">` with the secret).

    Body: `{"type": "batch.delivered", "data": {...}}`, where `data` has the fields of
    `POST /v1/batches`. `allocation_id` may be left out if the source has exactly one active
    allocation. Sending the same `webhook-id` again returns the first result
    (`duplicate: true`); a new message with the same `external_ref` updates the batch.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | InboundResult]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | InboundResult | None:
    """Receive a signed delivery message

     Called by the source's systems, not with an API key. Headers (Standard Webhooks):
    `webhook-id` (unique per message), `webhook-timestamp` (Unix seconds, within 5 minutes),
    `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">` with the secret).

    Body: `{"type": "batch.delivered", "data": {...}}`, where `data` has the fields of
    `POST /v1/batches`. `allocation_id` may be left out if the source has exactly one active
    allocation. Sending the same `webhook-id` again returns the first result
    (`duplicate: true`); a new message with the same `external_ref` updates the batch.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | InboundResult
    """

    return sync_detailed(
        endpoint_id=endpoint_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | InboundResult]:
    """Receive a signed delivery message

     Called by the source's systems, not with an API key. Headers (Standard Webhooks):
    `webhook-id` (unique per message), `webhook-timestamp` (Unix seconds, within 5 minutes),
    `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">` with the secret).

    Body: `{"type": "batch.delivered", "data": {...}}`, where `data` has the fields of
    `POST /v1/batches`. `allocation_id` may be left out if the source has exactly one active
    allocation. Sending the same `webhook-id` again returns the first result
    (`duplicate: true`); a new message with the same `external_ref` updates the batch.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | InboundResult]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | InboundResult | None:
    """Receive a signed delivery message

     Called by the source's systems, not with an API key. Headers (Standard Webhooks):
    `webhook-id` (unique per message), `webhook-timestamp` (Unix seconds, within 5 minutes),
    `webhook-signature` (`v1,<base64 HMAC-SHA256 of "id.timestamp.body">` with the secret).

    Body: `{"type": "batch.delivered", "data": {...}}`, where `data` has the fields of
    `POST /v1/batches`. `allocation_id` may be left out if the source has exactly one active
    allocation. Sending the same `webhook-id` again returns the first result
    (`duplicate: true`); a new message with the same `external_ref` updates the batch.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | InboundResult
    """

    return (
        await asyncio_detailed(
            endpoint_id=endpoint_id,
            client=client,
        )
    ).parsed
