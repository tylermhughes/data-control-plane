from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.allocation import Allocation
from ...types import Response


def _get_kwargs(
    allocation_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/allocations/{allocation_id}/cancel".format(
            allocation_id=quote(str(allocation_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Allocation | Any | None:
    if response.status_code == 200:
        response_200 = Allocation.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Allocation | Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Allocation | Any]:
    """Cancel an allocation

     Planned or active → cancelled.

    Args:
        allocation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Allocation | Any]
    """

    kwargs = _get_kwargs(
        allocation_id=allocation_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
) -> Allocation | Any | None:
    """Cancel an allocation

     Planned or active → cancelled.

    Args:
        allocation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Allocation | Any
    """

    return sync_detailed(
        allocation_id=allocation_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Allocation | Any]:
    """Cancel an allocation

     Planned or active → cancelled.

    Args:
        allocation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Allocation | Any]
    """

    kwargs = _get_kwargs(
        allocation_id=allocation_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
) -> Allocation | Any | None:
    """Cancel an allocation

     Planned or active → cancelled.

    Args:
        allocation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Allocation | Any
    """

    return (
        await asyncio_detailed(
            allocation_id=allocation_id,
            client=client,
        )
    ).parsed
