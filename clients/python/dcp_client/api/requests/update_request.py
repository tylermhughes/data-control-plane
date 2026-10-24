from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.request import Request
from ...models.request_update import RequestUpdate
from ...types import Response


def _get_kwargs(
    request_id: str,
    *,
    body: RequestUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/requests/{request_id}".format(
            request_id=quote(str(request_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Request | None:
    if response.status_code == 200:
        response_200 = Request.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Request]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: RequestUpdate,
) -> Response[Any | Request]:
    """Update a request

     Draft and open requests only. Changing `spec_version_id` affects new allocations only;
    existing allocations keep the version they were quoted against.

    Args:
        request_id (str):
        body (RequestUpdate): Draft and open requests only. Fields you send are changed; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Request]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: RequestUpdate,
) -> Any | Request | None:
    """Update a request

     Draft and open requests only. Changing `spec_version_id` affects new allocations only;
    existing allocations keep the version they were quoted against.

    Args:
        request_id (str):
        body (RequestUpdate): Draft and open requests only. Fields you send are changed; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Request
    """

    return sync_detailed(
        request_id=request_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: RequestUpdate,
) -> Response[Any | Request]:
    """Update a request

     Draft and open requests only. Changing `spec_version_id` affects new allocations only;
    existing allocations keep the version they were quoted against.

    Args:
        request_id (str):
        body (RequestUpdate): Draft and open requests only. Fields you send are changed; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Request]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: RequestUpdate,
) -> Any | Request | None:
    """Update a request

     Draft and open requests only. Changing `spec_version_id` affects new allocations only;
    existing allocations keep the version they were quoted against.

    Args:
        request_id (str):
        body (RequestUpdate): Draft and open requests only. Fields you send are changed; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Request
    """

    return (
        await asyncio_detailed(
            request_id=request_id,
            client=client,
            body=body,
        )
    ).parsed
