from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.dataset_version import DatasetVersion
from ...models.dataset_version_create import DatasetVersionCreate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_id: str,
    *,
    body: DatasetVersionCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["idempotency-key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/datasets/{dataset_id}/versions".format(
            dataset_id=quote(str(dataset_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | DatasetVersion | None:
    if response.status_code == 201:
        response_201 = DatasetVersion.from_dict(response.json())

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


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | DatasetVersion]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: DatasetVersionCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | DatasetVersion]:
    """Create the next version (frozen)

     Freezes a set of **accepted** batches as the dataset's next version.

    By default it is compared against the dataset's previous version and starts from that
    version's batches, adding `batch_ids`. `new_vs_baseline` shows what the added batches
    cost: the spend behind this version's eval change.

    Args:
        dataset_id (str):
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DatasetVersion]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: DatasetVersionCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | DatasetVersion | None:
    """Create the next version (frozen)

     Freezes a set of **accepted** batches as the dataset's next version.

    By default it is compared against the dataset's previous version and starts from that
    version's batches, adding `batch_ids`. `new_vs_baseline` shows what the added batches
    cost: the spend behind this version's eval change.

    Args:
        dataset_id (str):
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DatasetVersion
    """

    return sync_detailed(
        dataset_id=dataset_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: DatasetVersionCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | DatasetVersion]:
    """Create the next version (frozen)

     Freezes a set of **accepted** batches as the dataset's next version.

    By default it is compared against the dataset's previous version and starts from that
    version's batches, adding `batch_ids`. `new_vs_baseline` shows what the added batches
    cost: the spend behind this version's eval change.

    Args:
        dataset_id (str):
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DatasetVersion]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    *,
    client: AuthenticatedClient,
    body: DatasetVersionCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | DatasetVersion | None:
    """Create the next version (frozen)

     Freezes a set of **accepted** batches as the dataset's next version.

    By default it is compared against the dataset's previous version and starts from that
    version's batches, adding `batch_ids`. `new_vs_baseline` shows what the added batches
    cost: the spend behind this version's eval change.

    Args:
        dataset_id (str):
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DatasetVersion
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
