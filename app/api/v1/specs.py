from typing import Annotated

from fastapi import APIRouter, Path, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.specs import (
    Spec,
    SpecCreate,
    SpecUpdate,
    SpecVersion,
    SpecVersionApprove,
    SpecVersionUpdate,
)
from app.services import specs

router = APIRouter(prefix="/specs", tags=["specs"])
VersionNumber = Annotated[int, Path(ge=1, description="Version number, e.g. 2.")]


@router.get("", summary="List specs", responses=READ_ERRORS)
def list_specs(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Spec]:
    rows, next_cursor = specs.list_specs(
        session, principal, project_id=project_id, limit=limit, cursor=cursor
    )
    return Page(data=[specs.to_schema(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Spec,
    summary="Create a spec",
    responses=WRITE_ERRORS,
)
def create_spec(
    body: SpecCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Spec | Response:
    """Creates the spec and its version 1 as a **draft**, from `first_version`.

    Coverage targets and acceptance rules must refer to attributes (and values) defined in
    the same version. Each attribute's target shares must add up to 1 (100%) or less."""
    if idem.replay:
        return idem.replay
    out = specs.to_schema(specs.create_spec(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{spec_id}", summary="Get a spec", responses=READ_ERRORS)
def get_spec(spec_id: str, session: SessionDep, principal: PrincipalDep) -> Spec:
    return specs.to_schema(specs.get_spec(session, principal, spec_id))


@router.patch("/{spec_id}", summary="Rename or re-describe a spec", responses=WRITE_ERRORS)
def update_spec(
    spec_id: str, body: SpecUpdate, session: SessionDep, principal: PrincipalDep
) -> Spec:
    out = specs.to_schema(specs.update_spec(session, principal, spec_id, body))
    session.commit()
    return out


@router.delete(
    "/{spec_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a spec and all its versions",
    responses=WRITE_ERRORS,
)
def delete_spec(spec_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """From M3 on, specs used by a request can't be deleted."""
    specs.delete_spec(session, principal, spec_id)
    session.commit()


@router.get("/{spec_id}/versions", summary="List a spec's versions", responses=READ_ERRORS)
def list_spec_versions(
    spec_id: str,
    session: SessionDep,
    principal: PrincipalDep,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[SpecVersion]:
    rows, next_cursor = specs.list_versions(session, principal, spec_id, limit=limit, cursor=cursor)
    return Page(data=[SpecVersion.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "/{spec_id}/versions",
    status_code=status.HTTP_201_CREATED,
    response_model=SpecVersion,
    summary="Start the next version (draft)",
    responses=WRITE_ERRORS,
)
def create_spec_version(
    spec_id: str,
    body: SpecVersionUpdate,
    session: SessionDep,
    principal: PrincipalDep,
    idem: IdempotencyDep,
) -> SpecVersion | Response:
    """The new draft starts as a copy of the latest version. Send only what changes; send
    `{}` to start from an exact copy. Fails if the spec already has a draft."""
    if idem.replay:
        return idem.replay
    out = SpecVersion.model_validate(specs.create_version(session, principal, spec_id, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get(
    "/{spec_id}/versions/{version}", summary="Get one version of a spec", responses=READ_ERRORS
)
def get_spec_version(
    spec_id: str, version: VersionNumber, session: SessionDep, principal: PrincipalDep
) -> SpecVersion:
    return SpecVersion.model_validate(specs.get_version(session, principal, spec_id, version))


@router.patch(
    "/{spec_id}/versions/{version}", summary="Edit a draft version", responses=WRITE_ERRORS
)
def update_spec_version(
    spec_id: str,
    version: VersionNumber,
    body: SpecVersionUpdate,
    session: SessionDep,
    principal: PrincipalDep,
) -> SpecVersion:
    """Drafts only. Fields you send replace the draft's; the rest are kept.
    Approved versions can't change (409)."""
    out = SpecVersion.model_validate(
        specs.update_version(session, principal, spec_id, version, body)
    )
    session.commit()
    return out


@router.post(
    "/{spec_id}/versions/{version}/approve",
    summary="Approve a draft (freezes it)",
    responses=WRITE_ERRORS,
)
def approve_spec_version(
    spec_id: str,
    version: VersionNumber,
    body: SpecVersionApprove,
    session: SessionDep,
    principal: PrincipalDep,
) -> SpecVersion:
    """After approval the version can never be edited or deleted. Records who approved it
    (`approved_by`) and which API key did it."""
    out = SpecVersion.model_validate(
        specs.approve_version(session, principal, spec_id, version, body)
    )
    session.commit()
    return out


@router.delete(
    "/{spec_id}/versions/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Discard a draft version",
    responses=WRITE_ERRORS,
)
def delete_spec_version(
    spec_id: str, version: VersionNumber, session: SessionDep, principal: PrincipalDep
) -> None:
    """Drafts only. Approved versions can never be deleted."""
    specs.delete_version(session, principal, spec_id, version)
    session.commit()
