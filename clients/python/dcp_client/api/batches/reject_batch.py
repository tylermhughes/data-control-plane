from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch import Batch
from ...models.batch_reject import BatchReject
from ...types import Response


def _get_kwargs(
    batch_id: str,
    *,
    body: BatchReject,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/batches/{batch_id}/reject".format(
            batch_id=quote(str(batch_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Batch | None:
    if response.status_code == 200:
        response_200 = Batch.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Batch]:
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
    body: BatchReject,
) -> Response[Any | Batch]:
    """Reject a batch

     Received, passed or failed → rejected, with a reason. Not while checks run. Final:
    afterwards only notes can change.

    Args:
        batch_id (str):
        body (BatchReject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Batch]
    """

    kwargs = _get_kwargs(
        batch_id=batch_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    batch_id: str,
    *,
    client: AuthenticatedClient,
    body: BatchReject,
) -> Any | Batch | None:
    """Reject a batch

     Received, passed or failed → rejected, with a reason. Not while checks run. Final:
    afterwards only notes can change.

    Args:
        batch_id (str):
        body (BatchReject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Batch
    """

    return sync_detailed(
        batch_id=batch_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    batch_id: str,
    *,
    client: AuthenticatedClient,
    body: BatchReject,
) -> Response[Any | Batch]:
    """Reject a batch

     Received, passed or failed → rejected, with a reason. Not while checks run. Final:
    afterwards only notes can change.

    Args:
        batch_id (str):
        body (BatchReject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Batch]
    """

    kwargs = _get_kwargs(
        batch_id=batch_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    batch_id: str,
    *,
    client: AuthenticatedClient,
    body: BatchReject,
) -> Any | Batch | None:
    """Reject a batch

     Received, passed or failed → rejected, with a reason. Not while checks run. Final:
    afterwards only notes can change.

    Args:
        batch_id (str):
        body (BatchReject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Batch
    """

    return (
        await asyncio_detailed(
            batch_id=batch_id,
            client=client,
            body=body,
        )
    ).parsed
