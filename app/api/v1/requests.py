from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.datasets import Coverage
from app.schemas.requests import Request, RequestCreate, RequestStatus, RequestUpdate
from app.services import coverage, requests

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", summary="List requests", responses=READ_ERRORS)
def list_requests(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    capability_id: Annotated[str | None, Query(description="Only for this capability.")] = None,
    status: Annotated[RequestStatus | None, Query(description="Only in this status.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Request]:
    rows, next_cursor = requests.list_requests(
        session,
        principal,
        project_id=project_id,
        capability_id=capability_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[requests.to_schema(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Request,
    summary="Create a request",
    responses=WRITE_ERRORS,
)
def create_request(
    body: RequestCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Request | Response:
    """A request asks for data to improve one capability. It starts as a **draft**; the
    project is taken from the capability. Attach an approved spec version, then open it."""
    if idem.replay:
        return idem.replay
    out = requests.to_schema(requests.create_request(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{request_id}", summary="Get a request", responses=READ_ERRORS)
def get_request(request_id: str, session: SessionDep, principal: PrincipalDep) -> Request:
    return requests.to_schema(requests.get_request(session, principal, request_id))


@router.patch("/{request_id}", summary="Update a request", responses=WRITE_ERRORS)
def update_request(
    request_id: str, body: RequestUpdate, session: SessionDep, principal: PrincipalDep
) -> Request:
    """Draft and open requests only. Changing `spec_version_id` affects new allocations only;
    existing allocations keep the version they were quoted against."""
    out = requests.to_schema(requests.update_request(session, principal, request_id, body))
    session.commit()
    return out


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a request",
    responses=WRITE_ERRORS,
)
def delete_request(request_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Only requests with no allocations. Otherwise cancel it."""
    requests.delete_request(session, principal, request_id)
    session.commit()


@router.post("/{request_id}/open", summary="Open a request", responses=WRITE_ERRORS)
def open_request(request_id: str, session: SessionDep, principal: PrincipalDep) -> Request:
    """Draft → open. Needs an approved spec version. Allocations can only be activated on
    open requests."""
    out = requests.to_schema(requests.open_request(session, principal, request_id))
    session.commit()
    return out


@router.post("/{request_id}/close", summary="Close a request", responses=WRITE_ERRORS)
def close_request(request_id: str, session: SessionDep, principal: PrincipalDep) -> Request:
    """Open → closed. Refused while any allocation is active. Allocations that never started
    (planned) are cancelled."""
    out = requests.to_schema(requests.close_request(session, principal, request_id))
    session.commit()
    return out


@router.post("/{request_id}/cancel", summary="Cancel a request", responses=WRITE_ERRORS)
def cancel_request(request_id: str, session: SessionDep, principal: PrincipalDep) -> Request:
    """Draft or open → cancelled. Its planned and active allocations are cancelled too;
    completed ones are kept as they are."""
    out = requests.to_schema(requests.cancel_request(session, principal, request_id))
    session.commit()
    return out


@router.get("/{request_id}/coverage", summary="Coverage vs targets", responses=READ_ERRORS)
def get_request_coverage(request_id: str, session: SessionDep, principal: PrincipalDep) -> Coverage:
    """All accepted batches of this request, against its current spec version's coverage
    targets. Values more than the spec's tolerance below target are `below` and listed in
    `gaps`."""
    return coverage.for_request(session, principal, request_id)
