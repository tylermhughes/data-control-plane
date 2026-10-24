from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_deliveries_status_type_0 import ListDeliveriesStatusType0
from ...models.page_webhook_delivery import PageWebhookDelivery
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    endpoint_id: None | str | Unset = UNSET,
    event_id: None | str | Unset = UNSET,
    status: ListDeliveriesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_endpoint_id: None | str | Unset
    if isinstance(endpoint_id, Unset):
        json_endpoint_id = UNSET
    else:
        json_endpoint_id = endpoint_id
    params["endpoint_id"] = json_endpoint_id

    json_event_id: None | str | Unset
    if isinstance(event_id, Unset):
        json_event_id = UNSET
    else:
        json_event_id = event_id
    params["event_id"] = json_event_id

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, ListDeliveriesStatusType0):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/webhook-deliveries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | PageWebhookDelivery | None:
    if response.status_code == 200:
        response_200 = PageWebhookDelivery.from_dict(response.json())

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

    if response.status_code == 422:
        response_422 = cast(Any, None)
        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | PageWebhookDelivery]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    endpoint_id: None | str | Unset = UNSET,
    event_id: None | str | Unset = UNSET,
    status: ListDeliveriesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageWebhookDelivery]:
    """List webhook deliveries

    Args:
        endpoint_id (None | str | Unset): Only to this endpoint.
        event_id (None | str | Unset): Only for this event.
        status (ListDeliveriesStatusType0 | None | Unset): Only this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageWebhookDelivery]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
        event_id=event_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    endpoint_id: None | str | Unset = UNSET,
    event_id: None | str | Unset = UNSET,
    status: ListDeliveriesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageWebhookDelivery | None:
    """List webhook deliveries

    Args:
        endpoint_id (None | str | Unset): Only to this endpoint.
        event_id (None | str | Unset): Only for this event.
        status (ListDeliveriesStatusType0 | None | Unset): Only this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageWebhookDelivery
    """

    return sync_detailed(
        client=client,
        endpoint_id=endpoint_id,
        event_id=event_id,
        status=status,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    endpoint_id: None | str | Unset = UNSET,
    event_id: None | str | Unset = UNSET,
    status: ListDeliveriesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageWebhookDelivery]:
    """List webhook deliveries

    Args:
        endpoint_id (None | str | Unset): Only to this endpoint.
        event_id (None | str | Unset): Only for this event.
        status (ListDeliveriesStatusType0 | None | Unset): Only this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageWebhookDelivery]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
        event_id=event_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    endpoint_id: None | str | Unset = UNSET,
    event_id: None | str | Unset = UNSET,
    status: ListDeliveriesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageWebhookDelivery | None:
    """List webhook deliveries

    Args:
        endpoint_id (None | str | Unset): Only to this endpoint.
        event_id (None | str | Unset): Only for this event.
        status (ListDeliveriesStatusType0 | None | Unset): Only this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageWebhookDelivery
    """

    return (
        await asyncio_detailed(
            client=client,
            endpoint_id=endpoint_id,
            event_id=event_id,
            status=status,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
