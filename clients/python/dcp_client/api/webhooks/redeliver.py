from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.webhook_delivery import WebhookDelivery
from ...types import Response


def _get_kwargs(
    delivery_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/webhook-deliveries/{delivery_id}/redeliver".format(
            delivery_id=quote(str(delivery_id), safe=""),
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
    delivery_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | WebhookDelivery]:
    """Send a delivery again

     Queues the same message again as a new delivery (same `webhook-id`, so receivers that
    skip duplicates will skip it). The original's log is kept.

    Args:
        delivery_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WebhookDelivery]
    """

    kwargs = _get_kwargs(
        delivery_id=delivery_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    delivery_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | WebhookDelivery | None:
    """Send a delivery again

     Queues the same message again as a new delivery (same `webhook-id`, so receivers that
    skip duplicates will skip it). The original's log is kept.

    Args:
        delivery_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WebhookDelivery
    """

    return sync_detailed(
        delivery_id=delivery_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    delivery_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | WebhookDelivery]:
    """Send a delivery again

     Queues the same message again as a new delivery (same `webhook-id`, so receivers that
    skip duplicates will skip it). The original's log is kept.

    Args:
        delivery_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WebhookDelivery]
    """

    kwargs = _get_kwargs(
        delivery_id=delivery_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    delivery_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | WebhookDelivery | None:
    """Send a delivery again

     Queues the same message again as a new delivery (same `webhook-id`, so receivers that
    skip duplicates will skip it). The original's log is kept.

    Args:
        delivery_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WebhookDelivery
    """

    return (
        await asyncio_detailed(
            delivery_id=delivery_id,
            client=client,
        )
    ).parsed
