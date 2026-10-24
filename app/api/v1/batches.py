from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.batches import (
    Batch,
    BatchAccept,
    BatchCreate,
    BatchReject,
    BatchStatus,
    BatchUpdate,
)
from app.schemas.common import Page
from app.schemas.datasets import Coverage
from app.services import batches, coverage

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("", summary="List batches", responses=READ_ERRORS)
def list_batches(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    request_id: Annotated[str | None, Query(description="Only for this request.")] = None,
    allocation_id: Annotated[str | None, Query(description="Only for this allocation.")] = None,
    data_source_id: Annotated[str | None, Query(description="Only from this source.")] = None,
    status: Annotated[BatchStatus | None, Query(description="Only in this status.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Batch]:
    rows, next_cursor = batches.list_batches(
        session,
        principal,
        project_id=project_id,
        request_id=request_id,
        allocation_id=allocation_id,
        data_source_id=data_source_id,
        status=status,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[Batch.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Batch,
    summary="Register a delivery (or import one decided elsewhere)",
    responses={**WRITE_ERRORS, 200: {"model": Batch, "description": "Existing batch re-imported"}},
)
def create_batch(
    body: BatchCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Batch | Response:
    """Records one delivery against an **active** allocation. It starts as `received`; accept
    or reject it with the actions below.

    **Importing from other systems** (a vendor's QA, Labelbox, ...): include `decision` to
    register a batch that is already accepted or rejected, and `external_ref` (the source's own
    id for the delivery). Sending the same `external_ref` again updates that batch (200) and
    records what changed; identical data changes nothing."""
    if idem.replay:
        return idem.replay
    batch, created = batches.create_batch(session, principal, body)
    out = Batch.model_validate(batch)
    code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    idem.save(session, code, out)
    session.commit()
    if created:
        return out
    return JSONResponse(jsonable_encoder(out), status_code=code)


@router.get("/{batch_id}", summary="Get a batch", responses=READ_ERRORS)
def get_batch(batch_id: str, session: SessionDep, principal: PrincipalDep) -> Batch:
    return Batch.model_validate(batches.get_batch(session, principal, batch_id))


@router.patch("/{batch_id}", summary="Update a batch", responses=WRITE_ERRORS)
def update_batch(
    batch_id: str, body: BatchUpdate, session: SessionDep, principal: PrincipalDep
) -> Batch:
    """Undecided (`received`) batches: any field. Accepted or rejected: notes only."""
    out = Batch.model_validate(batches.update_batch(session, principal, batch_id, body))
    session.commit()
    return out


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an undecided batch",
    responses=WRITE_ERRORS,
)
def delete_batch(batch_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Only batches still `received`. Decided batches are part of the record."""
    batches.delete_batch(session, principal, batch_id)
    session.commit()


@router.post("/{batch_id}/accept", summary="Accept a batch", responses=WRITE_ERRORS)
def accept_batch(
    batch_id: str, body: BatchAccept, session: SessionDep, principal: PrincipalDep
) -> Batch:
    """Received → accepted, keeping `accepted_count` of the delivered items. Optional
    `attribute_counts` must use the spec version's attributes and can't exceed the accepted
    count for any attribute. Final: afterwards only notes can change."""
    out = Batch.model_validate(batches.accept_batch(session, principal, batch_id, body))
    session.commit()
    return out


@router.post("/{batch_id}/reject", summary="Reject a batch", responses=WRITE_ERRORS)
def reject_batch(
    batch_id: str, body: BatchReject, session: SessionDep, principal: PrincipalDep
) -> Batch:
    """Received → rejected, with a reason. Final: afterwards only notes can change."""
    out = Batch.model_validate(batches.reject_batch(session, principal, batch_id, body))
    session.commit()
    return out


@router.get("/{batch_id}/coverage", summary="Coverage vs targets", responses=READ_ERRORS)
def get_coverage(batch_id: str, session: SessionDep, principal: PrincipalDep) -> Coverage:
    """This batch's accepted items per attribute value, against its spec version's coverage
    targets. Values more than the spec's tolerance below target are `below` and listed in
    `gaps`. Uses the batch's `attribute_counts`, so it's empty if none were recorded."""
    return coverage.for_batch(session, principal, batch_id)
