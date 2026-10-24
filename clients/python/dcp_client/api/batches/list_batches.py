from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_batches_status_type_0 import ListBatchesStatusType0
from ...models.page_batch import PageBatch
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    request_id: None | str | Unset = UNSET,
    allocation_id: None | str | Unset = UNSET,
    data_source_id: None | str | Unset = UNSET,
    status: ListBatchesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    json_request_id: None | str | Unset
    if isinstance(request_id, Unset):
        json_request_id = UNSET
    else:
        json_request_id = request_id
    params["request_id"] = json_request_id

    json_allocation_id: None | str | Unset
    if isinstance(allocation_id, Unset):
        json_allocation_id = UNSET
    else:
        json_allocation_id = allocation_id
    params["allocation_id"] = json_allocation_id

    json_data_source_id: None | str | Unset
    if isinstance(data_source_id, Unset):
        json_data_source_id = UNSET
    else:
        json_data_source_id = data_source_id
    params["data_source_id"] = json_data_source_id

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, ListBatchesStatusType0):
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
        "url": "/v1/batches",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | PageBatch | None:
    if response.status_code == 200:
        response_200 = PageBatch.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | PageBatch]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    request_id: None | str | Unset = UNSET,
    allocation_id: None | str | Unset = UNSET,
    data_source_id: None | str | Unset = UNSET,
    status: ListBatchesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageBatch]:
    """List batches

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        request_id (None | str | Unset): Only for this request.
        allocation_id (None | str | Unset): Only for this allocation.
        data_source_id (None | str | Unset): Only from this source.
        status (ListBatchesStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageBatch]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        request_id=request_id,
        allocation_id=allocation_id,
        data_source_id=data_source_id,
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
    project_id: None | str | Unset = UNSET,
    request_id: None | str | Unset = UNSET,
    allocation_id: None | str | Unset = UNSET,
    data_source_id: None | str | Unset = UNSET,
    status: ListBatchesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageBatch | None:
    """List batches

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        request_id (None | str | Unset): Only for this request.
        allocation_id (None | str | Unset): Only for this allocation.
        data_source_id (None | str | Unset): Only from this source.
        status (ListBatchesStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageBatch
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        request_id=request_id,
        allocation_id=allocation_id,
        data_source_id=data_source_id,
        status=status,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    request_id: None | str | Unset = UNSET,
    allocation_id: None | str | Unset = UNSET,
    data_source_id: None | str | Unset = UNSET,
    status: ListBatchesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageBatch]:
    """List batches

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        request_id (None | str | Unset): Only for this request.
        allocation_id (None | str | Unset): Only for this allocation.
        data_source_id (None | str | Unset): Only from this source.
        status (ListBatchesStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageBatch]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        request_id=request_id,
        allocation_id=allocation_id,
        data_source_id=data_source_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    request_id: None | str | Unset = UNSET,
    allocation_id: None | str | Unset = UNSET,
    data_source_id: None | str | Unset = UNSET,
    status: ListBatchesStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageBatch | None:
    """List batches

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        request_id (None | str | Unset): Only for this request.
        allocation_id (None | str | Unset): Only for this allocation.
        data_source_id (None | str | Unset): Only from this source.
        status (ListBatchesStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageBatch
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            request_id=request_id,
            allocation_id=allocation_id,
            data_source_id=data_source_id,
            status=status,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
