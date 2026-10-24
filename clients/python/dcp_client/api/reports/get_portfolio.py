import datetime
from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.portfolio import Portfolio
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: None | str | Unset = UNSET,
    since: datetime.datetime | None | Unset = UNSET,
    until: datetime.datetime | None | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: None | str | Unset
    if isinstance(project_id, Unset):
        json_project_id = UNSET
    else:
        json_project_id = project_id
    params["project_id"] = json_project_id

    json_since: None | str | Unset
    if isinstance(since, Unset):
        json_since = UNSET
    elif isinstance(since, datetime.datetime):
        json_since = since.isoformat()
    else:
        json_since = since
    params["since"] = json_since

    json_until: None | str | Unset
    if isinstance(until, Unset):
        json_until = UNSET
    elif isinstance(until, datetime.datetime):
        json_until = until.isoformat()
    else:
        json_until = until
    params["until"] = json_until

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/reports/portfolio",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Portfolio | None:
    if response.status_code == 200:
        response_200 = Portfolio.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Portfolio]:
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
    since: datetime.datetime | None | Unset = UNSET,
    until: datetime.datetime | None | Unset = UNSET,
) -> Response[Any | Portfolio]:
    """Which data spend improved the models

     Per capability and per source type: spend, usable units, cost per usable unit, eval
    change (in points, positive is better), points per 10K of spend and, per capability,
    value and ROI.

    **Eval change** counts each dataset version with a main-metric result whose baseline has
    one too. Its spend is what that version's new batches cost. **By source type**, eval
    change is an estimate: each version's change is split by each type's share of the items
    it added (`is_estimate: true`). Every row lists the versions and eval results it's based
    on, and `notes` explains anything missing.

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        since (datetime.datetime | None | Unset): Only batches and versions from this time on.
        until (datetime.datetime | None | Unset): Only before this time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Portfolio]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        since=since,
        until=until,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    since: datetime.datetime | None | Unset = UNSET,
    until: datetime.datetime | None | Unset = UNSET,
) -> Any | Portfolio | None:
    """Which data spend improved the models

     Per capability and per source type: spend, usable units, cost per usable unit, eval
    change (in points, positive is better), points per 10K of spend and, per capability,
    value and ROI.

    **Eval change** counts each dataset version with a main-metric result whose baseline has
    one too. Its spend is what that version's new batches cost. **By source type**, eval
    change is an estimate: each version's change is split by each type's share of the items
    it added (`is_estimate: true`). Every row lists the versions and eval results it's based
    on, and `notes` explains anything missing.

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        since (datetime.datetime | None | Unset): Only batches and versions from this time on.
        until (datetime.datetime | None | Unset): Only before this time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Portfolio
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        since=since,
        until=until,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    since: datetime.datetime | None | Unset = UNSET,
    until: datetime.datetime | None | Unset = UNSET,
) -> Response[Any | Portfolio]:
    """Which data spend improved the models

     Per capability and per source type: spend, usable units, cost per usable unit, eval
    change (in points, positive is better), points per 10K of spend and, per capability,
    value and ROI.

    **Eval change** counts each dataset version with a main-metric result whose baseline has
    one too. Its spend is what that version's new batches cost. **By source type**, eval
    change is an estimate: each version's change is split by each type's share of the items
    it added (`is_estimate: true`). Every row lists the versions and eval results it's based
    on, and `notes` explains anything missing.

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        since (datetime.datetime | None | Unset): Only batches and versions from this time on.
        until (datetime.datetime | None | Unset): Only before this time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Portfolio]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        since=since,
        until=until,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    project_id: None | str | Unset = UNSET,
    since: datetime.datetime | None | Unset = UNSET,
    until: datetime.datetime | None | Unset = UNSET,
) -> Any | Portfolio | None:
    """Which data spend improved the models

     Per capability and per source type: spend, usable units, cost per usable unit, eval
    change (in points, positive is better), points per 10K of spend and, per capability,
    value and ROI.

    **Eval change** counts each dataset version with a main-metric result whose baseline has
    one too. Its spend is what that version's new batches cost. **By source type**, eval
    change is an estimate: each version's change is split by each type's share of the items
    it added (`is_estimate: true`). Every row lists the versions and eval results it's based
    on, and `notes` explains anything missing.

    Args:
        project_id (None | str | Unset): Only items in this project. Project keys always see only
            theirs.
        since (datetime.datetime | None | Unset): Only batches and versions from this time on.
        until (datetime.datetime | None | Unset): Only before this time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Portfolio
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            since=since,
            until=until,
        )
    ).parsed
