from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.data_source import DataSource
from ...models.data_source_update import DataSourceUpdate
from ...types import Response


def _get_kwargs(
    source_id: str,
    *,
    body: DataSourceUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/data-sources/{source_id}".format(
            source_id=quote(str(source_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | DataSource | None:
    if response.status_code == 200:
        response_200 = DataSource.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | DataSource]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    source_id: str,
    *,
    client: AuthenticatedClient,
    body: DataSourceUpdate,
) -> Response[Any | DataSource]:
    """Update a data source

     Send `"rights_expires_at": null` to clear the expiry date.

    Args:
        source_id (str):
        body (DataSourceUpdate): Only the fields you send are changed. `kind` and project can't
            change.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DataSource]
    """

    kwargs = _get_kwargs(
        source_id=source_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    source_id: str,
    *,
    client: AuthenticatedClient,
    body: DataSourceUpdate,
) -> Any | DataSource | None:
    """Update a data source

     Send `"rights_expires_at": null` to clear the expiry date.

    Args:
        source_id (str):
        body (DataSourceUpdate): Only the fields you send are changed. `kind` and project can't
            change.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DataSource
    """

    return sync_detailed(
        source_id=source_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    source_id: str,
    *,
    client: AuthenticatedClient,
    body: DataSourceUpdate,
) -> Response[Any | DataSource]:
    """Update a data source

     Send `"rights_expires_at": null` to clear the expiry date.

    Args:
        source_id (str):
        body (DataSourceUpdate): Only the fields you send are changed. `kind` and project can't
            change.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DataSource]
    """

    kwargs = _get_kwargs(
        source_id=source_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    source_id: str,
    *,
    client: AuthenticatedClient,
    body: DataSourceUpdate,
) -> Any | DataSource | None:
    """Update a data source

     Send `"rights_expires_at": null` to clear the expiry date.

    Args:
        source_id (str):
        body (DataSourceUpdate): Only the fields you send are changed. `kind` and project can't
            change.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DataSource
    """

    return (
        await asyncio_detailed(
            source_id=source_id,
            client=client,
            body=body,
        )
    ).parsed
