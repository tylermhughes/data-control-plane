from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.data_source import DataSource
from ...models.data_source_create import DataSourceCreate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: DataSourceCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["idempotency-key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/data-sources",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | DataSource | None:
    if response.status_code == 201:
        response_201 = DataSource.from_dict(response.json())

        return response_201

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
    *,
    client: AuthenticatedClient,
    body: DataSourceCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | DataSource]:
    """Create a data source

     A data source is anywhere data comes from: a vendor, an expert network, a synthetic
    pipeline, an RL environment, an internal workflow, beta users or a licensed dataset.
    Rights fields are recorded now and enforced by the training gate later.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DataSourceCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DataSource]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: DataSourceCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | DataSource | None:
    """Create a data source

     A data source is anywhere data comes from: a vendor, an expert network, a synthetic
    pipeline, an RL environment, an internal workflow, beta users or a licensed dataset.
    Rights fields are recorded now and enforced by the training gate later.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DataSourceCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DataSource
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: DataSourceCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | DataSource]:
    """Create a data source

     A data source is anywhere data comes from: a vendor, an expert network, a synthetic
    pipeline, an RL environment, an internal workflow, beta users or a licensed dataset.
    Rights fields are recorded now and enforced by the training gate later.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DataSourceCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DataSource]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: DataSourceCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | DataSource | None:
    """Create a data source

     A data source is anywhere data comes from: a vendor, an expert network, a synthetic
    pipeline, an RL environment, an internal workflow, beta users or a licensed dataset.
    Rights fields are recorded now and enforced by the training gate later.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DataSourceCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DataSource
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
