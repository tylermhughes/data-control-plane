from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.page_dataset import PageDataset
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    capability_id: None | str | Unset = UNSET,
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
        "url": "/v1/datasets",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | PageDataset | None:
    if response.status_code == 200:
        response_200 = PageDataset.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | PageDataset]:
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
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageDataset]:
    """List datasets

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageDataset]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        capability_id=capability_id,
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
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageDataset | None:
    """List datasets

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageDataset
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        capability_id=capability_id,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    capability_id: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[Any | PageDataset]:
    """List datasets

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PageDataset]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        capability_id=capability_id,
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
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Any | PageDataset | None:
    """List datasets

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        capability_id (None | str | Unset): Only for this capability.
        limit (int | Unset): Maximum items per page. Default: 50.
        cursor (None | str | Unset): `next_cursor` from the previous page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PageDataset
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            capability_id=capability_id,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
