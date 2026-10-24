from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.spec import Spec
from ...models.spec_update import SpecUpdate
from ...types import Response


def _get_kwargs(
    spec_id: str,
    *,
    body: SpecUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/specs/{spec_id}".format(
            spec_id=quote(str(spec_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Spec | None:
    if response.status_code == 200:
        response_200 = Spec.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Spec]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    spec_id: str,
    *,
    client: AuthenticatedClient,
    body: SpecUpdate,
) -> Response[Any | Spec]:
    """Rename or re-describe a spec

    Args:
        spec_id (str):
        body (SpecUpdate): Renames or re-describes the spec. Content changes go into versions.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Spec]
    """

    kwargs = _get_kwargs(
        spec_id=spec_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    spec_id: str,
    *,
    client: AuthenticatedClient,
    body: SpecUpdate,
) -> Any | Spec | None:
    """Rename or re-describe a spec

    Args:
        spec_id (str):
        body (SpecUpdate): Renames or re-describes the spec. Content changes go into versions.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Spec
    """

    return sync_detailed(
        spec_id=spec_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    spec_id: str,
    *,
    client: AuthenticatedClient,
    body: SpecUpdate,
) -> Response[Any | Spec]:
    """Rename or re-describe a spec

    Args:
        spec_id (str):
        body (SpecUpdate): Renames or re-describes the spec. Content changes go into versions.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Spec]
    """

    kwargs = _get_kwargs(
        spec_id=spec_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    spec_id: str,
    *,
    client: AuthenticatedClient,
    body: SpecUpdate,
) -> Any | Spec | None:
    """Rename or re-describe a spec

    Args:
        spec_id (str):
        body (SpecUpdate): Renames or re-describes the spec. Content changes go into versions.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Spec
    """

    return (
        await asyncio_detailed(
            spec_id=spec_id,
            client=client,
            body=body,
        )
    ).parsed
