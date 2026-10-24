from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.spec import Spec
from ...models.spec_create import SpecCreate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SpecCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["idempotency-key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/specs",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Spec | None:
    if response.status_code == 201:
        response_201 = Spec.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Spec]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: SpecCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | Spec]:
    """Create a spec

     Creates the spec and its version 1 as a **draft**, from `first_version`.

    Coverage targets and acceptance rules must refer to attributes (and values) defined in
    the same version. Each attribute's target shares must add up to 1 (100%) or less.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (SpecCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Spec]
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
    body: SpecCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | Spec | None:
    """Create a spec

     Creates the spec and its version 1 as a **draft**, from `first_version`.

    Coverage targets and acceptance rules must refer to attributes (and values) defined in
    the same version. Each attribute's target shares must add up to 1 (100%) or less.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (SpecCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Spec
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: SpecCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Response[Any | Spec]:
    """Create a spec

     Creates the spec and its version 1 as a **draft**, from `first_version`.

    Coverage targets and acceptance rules must refer to attributes (and values) defined in
    the same version. Each attribute's target shares must add up to 1 (100%) or less.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (SpecCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Spec]
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
    body: SpecCreate,
    idempotency_key: None | str | Unset = UNSET,
) -> Any | Spec | None:
    """Create a spec

     Creates the spec and its version 1 as a **draft**, from `first_version`.

    Coverage targets and acceptance rules must refer to attributes (and values) defined in
    the same version. Each attribute's target shares must add up to 1 (100%) or less.

    Args:
        idempotency_key (None | str | Unset): Any unique value, e.g. a UUID or `ci-run-42`
            (letters, digits and `. _ : -`, up to 255 characters). Retrying with the same key returns
            the original response instead of creating a duplicate. Leave empty if you don't need it.
        body (SpecCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Spec
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
