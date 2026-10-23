from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.requests import Allocation, AllocationCreate, AllocationStatus, AllocationUpdate
from app.services import allocations

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.get("", summary="List allocations", responses=READ_ERRORS)
def list_allocations(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    request_id: Annotated[str | None, Query(description="Only for this request.")] = None,
    data_source_id: Annotated[str | None, Query(description="Only for this source.")] = None,
    status: Annotated[AllocationStatus | None, Query(description="Only in this status.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Allocation]:
    rows, next_cursor = allocations.list_allocations(
        session,
        principal,
        project_id=project_id,
        request_id=request_id,
        data_source_id=data_source_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[Allocation.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Allocation,
    summary="Create an allocation",
    responses=WRITE_ERRORS,
)
def create_allocation(
    body: AllocationCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Allocation | Response:
    """Gives part of a request to one data source at a quoted rate. Starts as **planned**.

    The request needs an approved spec version; the allocation pins that exact version.
    Allocations may add up to more than the request's quantity (e.g. to cover rejects)."""
    if idem.replay:
        return idem.replay
    out = Allocation.model_validate(allocations.create_allocation(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{allocation_id}", summary="Get an allocation", responses=READ_ERRORS)
def get_allocation(allocation_id: str, session: SessionDep, principal: PrincipalDep) -> Allocation:
    return Allocation.model_validate(allocations.get_allocation(session, principal, allocation_id))


@router.patch("/{allocation_id}", summary="Update an allocation", responses=WRITE_ERRORS)
def update_allocation(
    allocation_id: str, body: AllocationUpdate, session: SessionDep, principal: PrincipalDep
) -> Allocation:
    """Planned: any field. Active: only `quantity`, `due_date` and `notes` (the quoted rate,
    currency and unit are the commitment). Complete or cancelled: nothing."""
    out = Allocation.model_validate(
        allocations.update_allocation(session, principal, allocation_id, body)
    )
    session.commit()
    return out


@router.delete(
    "/{allocation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a planned allocation",
    responses=WRITE_ERRORS,
)
def delete_allocation(allocation_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Planned allocations only. Cancel active ones instead."""
    allocations.delete_allocation(session, principal, allocation_id)
    session.commit()


@router.post("/{allocation_id}/activate", summary="Start the work", responses=WRITE_ERRORS)
def activate_allocation(
    allocation_id: str, session: SessionDep, principal: PrincipalDep
) -> Allocation:
    """Planned → active. The request must be open."""
    out = Allocation.model_validate(
        allocations.activate_allocation(session, principal, allocation_id)
    )
    session.commit()
    return out


@router.post("/{allocation_id}/complete", summary="Mark the work complete", responses=WRITE_ERRORS)
def complete_allocation(
    allocation_id: str, session: SessionDep, principal: PrincipalDep
) -> Allocation:
    """Active → complete."""
    out = Allocation.model_validate(
        allocations.complete_allocation(session, principal, allocation_id)
    )
    session.commit()
    return out


@router.post("/{allocation_id}/cancel", summary="Cancel an allocation", responses=WRITE_ERRORS)
def cancel_allocation(
    allocation_id: str, session: SessionDep, principal: PrincipalDep
) -> Allocation:
    """Planned or active → cancelled."""
    out = Allocation.model_validate(
        allocations.cancel_allocation(session, principal, allocation_id)
    )
    session.commit()
    return out
