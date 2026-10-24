from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.webhook_delivery import WebhookDelivery
from ...types import Response


def _get_kwargs(
    endpoint_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/webhook-endpoints/{endpoint_id}/test".format(
            endpoint_id=quote(str(endpoint_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | WebhookDelivery | None:
    if response.status_code == 202:
        response_202 = WebhookDelivery.from_dict(response.json())

        return response_202

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
) -> Response[Any | WebhookDelivery]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | WebhookDelivery]:
    """Send a test message

     Queues a `webhook.test` message for this endpoint; the worker sends it within about a
    second. Check the result with `GET /v1/webhook-deliveries/{id}`.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WebhookDelivery]
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
    client: AuthenticatedClient,
) -> Any | WebhookDelivery | None:
    """Send a test message

     Queues a `webhook.test` message for this endpoint; the worker sends it within about a
    second. Check the result with `GET /v1/webhook-deliveries/{id}`.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WebhookDelivery
    """

    return sync_detailed(
        endpoint_id=endpoint_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | WebhookDelivery]:
    """Send a test message

     Queues a `webhook.test` message for this endpoint; the worker sends it within about a
    second. Check the result with `GET /v1/webhook-deliveries/{id}`.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WebhookDelivery]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    endpoint_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | WebhookDelivery | None:
    """Send a test message

     Queues a `webhook.test` message for this endpoint; the worker sends it within about a
    second. Check the result with `GET /v1/webhook-deliveries/{id}`.

    Args:
        endpoint_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WebhookDelivery
    """

    return (
        await asyncio_detailed(
            endpoint_id=endpoint_id,
            client=client,
        )
    ).parsed
