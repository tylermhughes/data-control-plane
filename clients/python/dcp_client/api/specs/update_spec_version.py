from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.spec_version import SpecVersion
from ...models.spec_version_update import SpecVersionUpdate
from ...types import Response


def _get_kwargs(
    spec_id: str,
    version: int,
    *,
    body: SpecVersionUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/specs/{spec_id}/versions/{version}".format(
            spec_id=quote(str(spec_id), safe=""),
            version=quote(str(version), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | SpecVersion | None:
    if response.status_code == 200:
        response_200 = SpecVersion.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | SpecVersion]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    spec_id: str,
    version: int,
    *,
    client: AuthenticatedClient,
    body: SpecVersionUpdate,
) -> Response[Any | SpecVersion]:
    """Edit a draft version

     Drafts only. Fields you send replace the draft's; the rest are kept.
    Approved versions can't change (409).

    Args:
        spec_id (str):
        version (int): Version number, e.g. 2.
        body (SpecVersionUpdate): For drafts only. Fields you send replace the draft's; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SpecVersion]
    """

    kwargs = _get_kwargs(
        spec_id=spec_id,
        version=version,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    spec_id: str,
    version: int,
    *,
    client: AuthenticatedClient,
    body: SpecVersionUpdate,
) -> Any | SpecVersion | None:
    """Edit a draft version

     Drafts only. Fields you send replace the draft's; the rest are kept.
    Approved versions can't change (409).

    Args:
        spec_id (str):
        version (int): Version number, e.g. 2.
        body (SpecVersionUpdate): For drafts only. Fields you send replace the draft's; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SpecVersion
    """

    return sync_detailed(
        spec_id=spec_id,
        version=version,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    spec_id: str,
    version: int,
    *,
    client: AuthenticatedClient,
    body: SpecVersionUpdate,
) -> Response[Any | SpecVersion]:
    """Edit a draft version

     Drafts only. Fields you send replace the draft's; the rest are kept.
    Approved versions can't change (409).

    Args:
        spec_id (str):
        version (int): Version number, e.g. 2.
        body (SpecVersionUpdate): For drafts only. Fields you send replace the draft's; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SpecVersion]
    """

    kwargs = _get_kwargs(
        spec_id=spec_id,
        version=version,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    spec_id: str,
    version: int,
    *,
    client: AuthenticatedClient,
    body: SpecVersionUpdate,
) -> Any | SpecVersion | None:
    """Edit a draft version

     Drafts only. Fields you send replace the draft's; the rest are kept.
    Approved versions can't change (409).

    Args:
        spec_id (str):
        version (int): Version number, e.g. 2.
        body (SpecVersionUpdate): For drafts only. Fields you send replace the draft's; the rest
            are kept.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SpecVersion
    """

    return (
        await asyncio_detailed(
            spec_id=spec_id,
            version=version,
            client=client,
            body=body,
        )
    ).parsed
