from fastapi import APIRouter, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.capabilities import Capability, CapabilityCreate, CapabilityUpdate
from app.schemas.common import Page
from app.services import capabilities

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", summary="List capabilities", responses=READ_ERRORS)
def list_capabilities(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Capability]:
    rows, next_cursor = capabilities.list_capabilities(
        session, principal, project_id=project_id, limit=limit, cursor=cursor
    )
    return Page(data=[Capability.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Capability,
    summary="Create a capability",
    responses=WRITE_ERRORS,
)
def create_capability(
    body: CapabilityCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Capability | Response:
    """A capability is something the data should improve, measured by one main eval metric.
    `value_per_point` is what one point of improvement is worth; reports use it for ROI."""
    if idem.replay:
        return idem.replay
    out = Capability.model_validate(capabilities.create_capability(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{capability_id}", summary="Get a capability", responses=READ_ERRORS)
def get_capability(capability_id: str, session: SessionDep, principal: PrincipalDep) -> Capability:
    return Capability.model_validate(capabilities.get_capability(session, principal, capability_id))


@router.patch("/{capability_id}", summary="Update a capability", responses=WRITE_ERRORS)
def update_capability(
    capability_id: str, body: CapabilityUpdate, session: SessionDep, principal: PrincipalDep
) -> Capability:
    out = Capability.model_validate(
        capabilities.update_capability(session, principal, capability_id, body)
    )
    session.commit()
    return out


@router.delete(
    "/{capability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a capability",
    responses=WRITE_ERRORS,
)
def delete_capability(capability_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    capabilities.delete_capability(session, principal, capability_id)
    session.commit()
