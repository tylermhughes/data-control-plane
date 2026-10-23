"""Specs and their versions.

Lifecycle: every version starts as a draft; approving it freezes it for good. A spec has at
most one draft at a time. A new version starts as a copy of the latest one.
"""

from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid, NotFound
from app.ids import new_id
from app.models import Spec, SpecVersion
from app.models.base import utcnow
from app.schemas import specs as schemas
from app.services import events, scoped
from app.services.pagination import paginate
from app.services.principal import Principal

LABEL = "spec"
CONTENT_FIELDS = tuple(schemas.SpecContent.model_fields)


def to_schema(spec: Spec) -> schemas.Spec:
    numbers = [v.version for v in spec.versions]
    approved = [v.version for v in spec.versions if v.status == "approved"]
    drafts = [v.version for v in spec.versions if v.status == "draft"]
    return schemas.Spec(
        id=spec.id,
        project_id=spec.project_id,
        name=spec.name,
        description=spec.description,
        latest_version=max(numbers, default=0),
        latest_approved_version=max(approved, default=None),
        draft_version=drafts[0] if drafts else None,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


def _emit_spec(session: Session, type: str, spec: Spec, actor: Principal) -> None:
    events.emit(
        session, type, to_schema(spec), subject_id=spec.id, project_id=spec.project_id, actor=actor
    )


def _emit_version(session: Session, type: str, version: SpecVersion, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.SpecVersion.model_validate(version),
        subject_id=version.id,
        project_id=version.spec.project_id,
        actor=actor,
    )


# --- specs -----------------------------------------------------------------------------------


def list_specs(
    session: Session, actor: Principal, *, project_id: str | None, limit: int, cursor: str | None
) -> tuple[Sequence[Spec], str | None]:
    return scoped.list_scoped(
        session, actor, Spec, project_id=project_id, limit=limit, cursor=cursor
    )


def get_spec(session: Session, actor: Principal, spec_id: str) -> Spec:
    return scoped.get_scoped(session, actor, Spec, spec_id, LABEL)


def create_spec(session: Session, actor: Principal, body: schemas.SpecCreate) -> Spec:
    actor.require_write()
    project_id = scoped.resolve_project_id(session, actor, body.project_id)
    scoped.check_name_free(session, Spec, project_id, body.name, LABEL)
    spec = Spec(
        id=new_id("spc"), project_id=project_id, name=body.name, description=body.description
    )
    session.add(spec)
    session.flush()
    version = _new_version(spec, 1, body.first_version.model_dump(mode="json"))
    session.add(version)
    session.flush()
    session.refresh(spec, ["versions"])
    _emit_spec(session, "spec.created", spec, actor)
    _emit_version(session, "spec_version.created", version, actor)
    return spec


def update_spec(session: Session, actor: Principal, spec_id: str, body: schemas.SpecUpdate) -> Spec:
    spec = get_spec(session, actor, spec_id)
    actor.require_write()
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if changes.get("name", spec.name) != spec.name:
        scoped.check_name_free(session, Spec, spec.project_id, changes["name"], LABEL)
    scoped.apply_changes(spec, changes)
    session.flush()
    _emit_spec(session, "spec.updated", spec, actor)
    return spec


def delete_spec(session: Session, actor: Principal, spec_id: str) -> None:
    spec = get_spec(session, actor, spec_id)
    actor.require_write()
    _emit_spec(session, "spec.deleted", spec, actor)
    session.delete(spec)
    session.flush()


# --- versions --------------------------------------------------------------------------------


def _new_version(spec: Spec, number: int, content: dict[str, Any]) -> SpecVersion:
    return SpecVersion(id=new_id("spv"), spec=spec, version=number, status="draft", **content)


def _content_of(version: SpecVersion) -> dict[str, Any]:
    return {field: getattr(version, field) for field in CONTENT_FIELDS}


def list_versions(
    session: Session, actor: Principal, spec_id: str, *, limit: int, cursor: str | None
) -> tuple[Sequence[SpecVersion], str | None]:
    get_spec(session, actor, spec_id)
    stmt = select(SpecVersion).where(SpecVersion.spec_id == spec_id)
    return paginate(session, stmt, SpecVersion.id, limit=limit, cursor=cursor)


def get_version(session: Session, actor: Principal, spec_id: str, number: int) -> SpecVersion:
    spec = get_spec(session, actor, spec_id)
    for version in spec.versions:
        if version.version == number:
            return version
    raise NotFound(f"Spec '{spec_id}' has no version {number}.")


def create_version(
    session: Session, actor: Principal, spec_id: str, body: schemas.SpecVersionUpdate
) -> SpecVersion:
    """Start the next draft as a copy of the latest version, with the given fields replaced."""
    spec = get_spec(session, actor, spec_id)
    actor.require_write()
    if any(v.status == "draft" for v in spec.versions):
        raise Conflict("This spec already has a draft. Edit or approve it first.")
    latest = spec.versions[-1]
    content = _validated_content(_content_of(latest), body)
    content["change_note"] = body.change_note or ""
    version = _new_version(spec, latest.version + 1, content)
    session.add(version)
    session.flush()
    _emit_version(session, "spec_version.created", version, actor)
    return version


def update_version(
    session: Session,
    actor: Principal,
    spec_id: str,
    number: int,
    body: schemas.SpecVersionUpdate,
) -> SpecVersion:
    version = get_version(session, actor, spec_id, number)
    actor.require_write()
    _require_draft(version)
    scoped.apply_changes(version, _validated_content(_content_of(version), body))
    session.flush()
    _emit_version(session, "spec_version.updated", version, actor)
    return version


def approve_version(
    session: Session,
    actor: Principal,
    spec_id: str,
    number: int,
    body: schemas.SpecVersionApprove,
) -> SpecVersion:
    version = get_version(session, actor, spec_id, number)
    actor.require_write()
    _require_draft(version)
    version.status = "approved"
    version.approved_by = body.approved_by
    version.approved_by_key_id = actor.key_id
    version.approved_at = utcnow()
    session.flush()
    _emit_version(session, "spec_version.approved", version, actor)
    return version


def delete_version(session: Session, actor: Principal, spec_id: str, number: int) -> None:
    version = get_version(session, actor, spec_id, number)
    actor.require_write()
    _require_draft(version)
    if len(version.spec.versions) == 1:
        raise Conflict("This is the spec's only version. Delete the spec instead.")
    _emit_version(session, "spec_version.deleted", version, actor)
    version.spec.versions.remove(version)
    session.flush()


def _require_draft(version: SpecVersion) -> None:
    if version.status != "draft":
        raise Conflict(
            f"Version {version.version} is approved and can't change. Create a new version instead."
        )


def _validated_content(current: dict[str, Any], body: schemas.SpecVersionUpdate) -> dict[str, Any]:
    """Merge the changes into the current content and re-check it as a whole."""
    merged = {**current, **body.model_dump(exclude_unset=True, mode="json")}
    try:
        return schemas.SpecContent.model_validate(merged).model_dump(mode="json")
    except ValidationError as exc:
        raise Invalid(
            "; ".join(e["msg"].removeprefix("Value error, ") for e in exc.errors())
        ) from exc
