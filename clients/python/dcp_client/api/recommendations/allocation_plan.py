from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.allocation_plan import AllocationPlan
from ...types import Response


def _get_kwargs(
    request_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/requests/{request_id}/allocation-plan".format(
            request_id=quote(str(request_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> AllocationPlan | Any | None:
    if response.status_code == 200:
        response_200 = AllocationPlan.from_dict(response.json())

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
) -> Response[AllocationPlan | Any]:
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
) -> Response[AllocationPlan | Any]:
    """Suggest how to split a request across sources

     A suggested split of the request's remaining units across the project's sources, from
    their last 90 days: cost per usable unit, accept rate, throughput, what they already owe,
    rights and attribute mix. Untested sources get a small pilot. Each suggestion includes an
    `allocation` ready for `POST /v1/allocations`. Nothing is created until you do that.

    Args:
        request_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AllocationPlan | Any]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    request_id: str,
    *,
    client: AuthenticatedClient,
) -> AllocationPlan | Any | None:
    """Suggest how to split a request across sources

     A suggested split of the request's remaining units across the project's sources, from
    their last 90 days: cost per usable unit, accept rate, throughput, what they already owe,
    rights and attribute mix. Untested sources get a small pilot. Each suggestion includes an
    `allocation` ready for `POST /v1/allocations`. Nothing is created until you do that.

    Args:
        request_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AllocationPlan | Any
    """

    return sync_detailed(
        request_id=request_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    request_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[AllocationPlan | Any]:
    """Suggest how to split a request across sources

     A suggested split of the request's remaining units across the project's sources, from
    their last 90 days: cost per usable unit, accept rate, throughput, what they already owe,
    rights and attribute mix. Untested sources get a small pilot. Each suggestion includes an
    `allocation` ready for `POST /v1/allocations`. Nothing is created until you do that.

    Args:
        request_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AllocationPlan | Any]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    request_id: str,
    *,
    client: AuthenticatedClient,
) -> AllocationPlan | Any | None:
    """Suggest how to split a request across sources

     A suggested split of the request's remaining units across the project's sources, from
    their last 90 days: cost per usable unit, accept rate, throughput, what they already owe,
    rights and attribute mix. Untested sources get a small pilot. Each suggestion includes an
    `allocation` ready for `POST /v1/allocations`. Nothing is created until you do that.

    Args:
        request_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AllocationPlan | Any
    """

    return (
        await asyncio_detailed(
            request_id=request_id,
            client=client,
        )
    ).parsed
