from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.spec_version import SpecVersion
from ...types import Response


def _get_kwargs(
    capability_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/capabilities/{capability_id}/diagnosis/draft-spec".format(
            capability_id=quote(str(capability_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | SpecVersion | None:
    if response.status_code == 201:
        response_201 = SpecVersion.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | SpecVersion]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    capability_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | SpecVersion]:
    """Draft the suggested spec change

     Creates the diagnosis's suggested coverage targets as a new **draft** version of the
    spec, marked as drafted by DCP. A person reviews, edits and approves it as usual. Refused
    if the diagnosis doesn't recommend refining the spec, or the spec already has a draft.

    Args:
        capability_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SpecVersion]
    """

    kwargs = _get_kwargs(
        capability_id=capability_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    capability_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | SpecVersion | None:
    """Draft the suggested spec change

     Creates the diagnosis's suggested coverage targets as a new **draft** version of the
    spec, marked as drafted by DCP. A person reviews, edits and approves it as usual. Refused
    if the diagnosis doesn't recommend refining the spec, or the spec already has a draft.

    Args:
        capability_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SpecVersion
    """

    return sync_detailed(
        capability_id=capability_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    capability_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | SpecVersion]:
    """Draft the suggested spec change

     Creates the diagnosis's suggested coverage targets as a new **draft** version of the
    spec, marked as drafted by DCP. A person reviews, edits and approves it as usual. Refused
    if the diagnosis doesn't recommend refining the spec, or the spec already has a draft.

    Args:
        capability_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SpecVersion]
    """

    kwargs = _get_kwargs(
        capability_id=capability_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    capability_id: str,
    *,
    client: AuthenticatedClient,
) -> Any | SpecVersion | None:
    """Draft the suggested spec change

     Creates the diagnosis's suggested coverage targets as a new **draft** version of the
    spec, marked as drafted by DCP. A person reviews, edits and approves it as usual. Refused
    if the diagnosis doesn't recommend refining the spec, or the spec already has a draft.

    Args:
        capability_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SpecVersion
    """

    return (
        await asyncio_detailed(
            capability_id=capability_id,
            client=client,
        )
    ).parsed
