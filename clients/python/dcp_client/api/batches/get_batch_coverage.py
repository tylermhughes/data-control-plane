from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.coverage import Coverage
from ...types import Response


def _get_kwargs(
    batch_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/batches/{batch_id}/coverage".format(
            batch_id=quote(str(batch_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Coverage | None:
    if response.status_code == 200:
        response_200 = Coverage.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Coverage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    batch_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | Coverage]:
    """Coverage vs targets

     This batch's accepted items per attribute value, against its spec version's coverage
    targets. Values more than the spec's tolerance below target are `below` and listed in
    `gaps`. Uses the batch's `attribute_counts`, so it's empty if none were recorded.

    Args:
        batch_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Coverage]
    """

    kwargs = _get_kwargs(
        batch_id=batch_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    batch_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | Coverage | None:
    """Coverage vs targets

     This batch's accepted items per attribute value, against its spec version's coverage
    targets. Values more than the spec's tolerance below target are `below` and listed in
    `gaps`. Uses the batch's `attribute_counts`, so it's empty if none were recorded.

    Args:
        batch_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Coverage
    """

    return sync_detailed(
        batch_id=batch_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    batch_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | Coverage]:
    """Coverage vs targets

     This batch's accepted items per attribute value, against its spec version's coverage
    targets. Values more than the spec's tolerance below target are `below` and listed in
    `gaps`. Uses the batch's `attribute_counts`, so it's empty if none were recorded.

    Args:
        batch_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Coverage]
    """

    kwargs = _get_kwargs(
        batch_id=batch_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    batch_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | Coverage | None:
    """Coverage vs targets

     This batch's accepted items per attribute value, against its spec version's coverage
    targets. Values more than the spec's tolerance below target are `below` and listed in
    `gaps`. Uses the batch's `attribute_counts`, so it's empty if none were recorded.

    Args:
        batch_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Coverage
    """

    return (
        await asyncio_detailed(
            batch_id=batch_id,
            client=client,
        )
    ).parsed
