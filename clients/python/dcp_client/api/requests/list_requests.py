from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_requests_status_type_0 import ListRequestsStatusType0
from ...models.page_request import PageRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    capability_id: None | str | Unset = UNSET,
    status: ListRequestsStatusType0 | None | Unset = UNSET,
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

    json_capability_id: None | str | Unset
    if isinstance(capability_id, Unset):
        json_capability_id = UNSET
    else:
        json_capability_id = capability_id
    params["capability_id"] = json_capability_id

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, ListRequestsStatusType0):
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
        "url": "/v1/requests",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | PageRequest | None:
    if response.status_code == 200:
        response_200 = PageRequest.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | PageRequest]:
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
    capability_id: None | str | Unset = UNSET,
    status: ListRequestsStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageRequest]:
    """List requests

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        status (ListRequestsStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageRequest]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        capability_id=capability_id,
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
    capability_id: None | str | Unset = UNSET,
    status: ListRequestsStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageRequest | None:
    """List requests

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        status (ListRequestsStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageRequest
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        capability_id=capability_id,
        status=status,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    capability_id: None | str | Unset = UNSET,
    status: ListRequestsStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageRequest]:
    """List requests

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        status (ListRequestsStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageRequest]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        capability_id=capability_id,
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
    capability_id: None | str | Unset = UNSET,
    status: ListRequestsStatusType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageRequest | None:
    """List requests

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        status (ListRequestsStatusType0 | None | Unset): Only in this status.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageRequest
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            capability_id=capability_id,
            status=status,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
