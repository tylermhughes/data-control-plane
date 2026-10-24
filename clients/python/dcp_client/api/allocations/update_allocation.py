from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.allocation import Allocation
from ...models.allocation_update import AllocationUpdate
from ...types import Response


def _get_kwargs(
    allocation_id: str,
    *,
    body: AllocationUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/allocations/{allocation_id}".format(
            allocation_id=quote(str(allocation_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    body: AllocationUpdate,
) -> Response[Allocation | Any]:
    """Update an allocation

     Planned: any field. Active: only `quantity`, `due_date` and `notes` (the quoted rate,
    currency and unit are the commitment). Complete or cancelled: nothing.

    Args:
        allocation_id (str):
        body (AllocationUpdate): Planned allocations: any field. Active: only quantity, due date
            and notes.
            Complete or cancelled: nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Allocation | Any]
    """

    kwargs = _get_kwargs(
        allocation_id=allocation_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
    body: AllocationUpdate,
) -> Allocation | Any | None:
    """Update an allocation

     Planned: any field. Active: only `quantity`, `due_date` and `notes` (the quoted rate,
    currency and unit are the commitment). Complete or cancelled: nothing.

    Args:
        allocation_id (str):
        body (AllocationUpdate): Planned allocations: any field. Active: only quantity, due date
            and notes.
            Complete or cancelled: nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Allocation | Any
    """

    return sync_detailed(
        allocation_id=allocation_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
    body: AllocationUpdate,
) -> Response[Allocation | Any]:
    """Update an allocation

     Planned: any field. Active: only `quantity`, `due_date` and `notes` (the quoted rate,
    currency and unit are the commitment). Complete or cancelled: nothing.

    Args:
        allocation_id (str):
        body (AllocationUpdate): Planned allocations: any field. Active: only quantity, due date
            and notes.
            Complete or cancelled: nothing.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Allocation | Any]
    """

    kwargs = _get_kwargs(
        allocation_id=allocation_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    allocation_id: str,
    *,
    client: AuthenticatedClient,
    body: AllocationUpdate,
) -> Allocation | Any | None:
    """Update an allocation

     Planned: any field. Active: only `quantity`, `due_date` and `notes` (the quoted rate,
    currency and unit are the commitment). Complete or cancelled: nothing.

    Args:
        allocation_id (str):
        body (AllocationUpdate): Planned allocations: any field. Active: only quantity, due date
            and notes.
            Complete or cancelled: nothing.

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
            body=body,
        )
    ).parsed
