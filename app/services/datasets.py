"""Datasets, their frozen versions, manifests and eval results.

A dataset version is created complete and never changes: a list of accepted batches plus the
baseline it's compared against (by default the dataset's previous version, keeping the
baseline's batches and adding new ones).
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid
from app.ids import new_id
from app.models import Batch, Capability, Dataset, DatasetVersion, EvalResult
from app.models.base import utcnow
from app.schemas import datasets as schemas
from app.services import events, scoped
from app.services.principal import Principal


def unit_totals(batches: Iterable[Batch]) -> list[schemas.UnitTotal]:
    totals: dict[tuple[str, str], list[Decimal]] = defaultdict(lambda: [Decimal(0)] * 3)
    for b in batches:
        total = totals[(b.allocation.unit, b.currency)]
        total[0] += 1
        total[1] += b.accepted_count or 0
        total[2] += b.spend
    return [
        schemas.UnitTotal(
            unit=unit, currency=currency, batch_count=int(n), accepted_count=int(acc), spend=spend
        )
        for (unit, currency), (n, acc, spend) in sorted(totals.items())
    ]


# --- datasets --------------------------------------------------------------------------------


def dataset_schema(ds: Dataset) -> schemas.Dataset:
    return schemas.Dataset(
        id=ds.id,
        project_id=ds.project_id,
        capability_id=ds.capability_id,
        name=ds.name,
        description=ds.description,
        latest_version=max((v.version for v in ds.versions), default=0),
        created_at=ds.created_at,
        updated_at=ds.updated_at,
    )


def _emit_dataset(session: Session, type: str, ds: Dataset, actor: Principal) -> None:
    events.emit(
        session, type, dataset_schema(ds), subject_id=ds.id, project_id=ds.project_id, actor=actor
    )


def list_datasets(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    capability_id: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Dataset], str | None]:
    where = [Dataset.capability_id == capability_id] if capability_id else []
    return scoped.list_scoped(
        session, actor, Dataset, project_id=project_id, limit=limit, cursor=cursor, where=where
    )


def get_dataset(session: Session, actor: Principal, dataset_id: str) -> Dataset:
    return scoped.get_scoped(session, actor, Dataset, dataset_id, "dataset")


def create_dataset(session: Session, actor: Principal, body: schemas.DatasetCreate) -> Dataset:
    actor.require_write()
    cap = session.get(Capability, body.capability_id)
    if cap is None or not actor.can_see_project(cap.project_id):
        raise Invalid(f"No capability with id '{body.capability_id}'.")
    scoped.check_name_free(session, Dataset, cap.project_id, body.name, "dataset")
    ds = Dataset(
        id=new_id("dst"),
        project_id=cap.project_id,
        capability_id=cap.id,
        name=body.name,
        description=body.description,
    )
    session.add(ds)
    session.flush()
    session.refresh(ds, ["versions"])
    _emit_dataset(session, "dataset.created", ds, actor)
    return ds


def update_dataset(
    session: Session, actor: Principal, dataset_id: str, body: schemas.DatasetUpdate
) -> Dataset:
    ds = get_dataset(session, actor, dataset_id)
    actor.require_write()
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if changes.get("name", ds.name) != ds.name:
        scoped.check_name_free(session, Dataset, ds.project_id, changes["name"], "dataset")
    scoped.apply_changes(ds, changes)
    session.flush()
    _emit_dataset(session, "dataset.updated", ds, actor)
    return ds


def delete_dataset(session: Session, actor: Principal, dataset_id: str) -> None:
    ds = get_dataset(session, actor, dataset_id)
    actor.require_write()
    if ds.versions:
        raise Conflict(f"This dataset has {len(ds.versions)} version(s). Delete them first.")
    _emit_dataset(session, "dataset.deleted", ds, actor)
    session.delete(ds)
    session.flush()


# --- versions --------------------------------------------------------------------------------


def version_schema(v: DatasetVersion) -> schemas.DatasetVersion:
    return schemas.DatasetVersion(
        id=v.id,
        project_id=v.project_id,
        dataset_id=v.dataset_id,
        capability_id=v.capability_id,
        version=v.version,
        baseline_version_id=v.baseline_version_id,
        batch_ids=v.batch_ids,
        totals=unit_totals(v.batches),
        new_vs_baseline=unit_totals(v.new_batches()),
        notes=v.notes,
        created_at=v.created_at,
    )


def _emit_version(session: Session, type: str, v: DatasetVersion, actor: Principal) -> None:
    events.emit(
        session, type, version_schema(v), subject_id=v.id, project_id=v.project_id, actor=actor
    )


def list_versions(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    dataset_id: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[DatasetVersion], str | None]:
    where = [DatasetVersion.dataset_id == dataset_id] if dataset_id else []
    return scoped.list_scoped(
        session,
        actor,
        DatasetVersion,
        project_id=project_id,
        limit=limit,
        cursor=cursor,
        where=where,
    )


def get_version(session: Session, actor: Principal, version_id: str) -> DatasetVersion:
    return scoped.get_scoped(session, actor, DatasetVersion, version_id, "dataset version")


def create_version(
    session: Session, actor: Principal, dataset_id: str, body: schemas.DatasetVersionCreate
) -> DatasetVersion:
    ds = get_dataset(session, actor, dataset_id)
    actor.require_write()

    baseline: DatasetVersion | None
    if "baseline_version_id" in body.model_fields_set:
        baseline = None
        if body.baseline_version_id is not None:
            baseline = session.get(DatasetVersion, body.baseline_version_id)
            if baseline is None or baseline.project_id != ds.project_id:
                raise Invalid(f"No dataset version with id '{body.baseline_version_id}'.")
            if baseline.capability_id != ds.capability_id:
                raise Invalid("The baseline must be a version for the same capability.")
    else:
        baseline = ds.versions[-1] if ds.versions else None

    chosen: dict[str, Batch] = {}
    if baseline is not None and body.include_baseline_batches:
        chosen.update((b.id, b) for b in baseline.batches)
    for batch_id in body.batch_ids:
        batch = session.get(Batch, batch_id)
        if batch is None or batch.project_id != ds.project_id:
            raise Invalid(f"No batch with id '{batch_id}' in this project.")
        if batch.status != "accepted":
            raise Invalid(f"Batch {batch_id} is {batch.status}; only accepted batches can be used.")
        chosen[batch.id] = batch
    if not chosen:
        raise Invalid("A dataset version needs at least one accepted batch.")

    version = DatasetVersion(
        id=new_id("dsv"),
        project_id=ds.project_id,
        dataset=ds,
        version=max((v.version for v in ds.versions), default=0) + 1,
        baseline=baseline,
        notes=body.notes,
        created_at=utcnow(),
    )
    version.batches = sorted(chosen.values(), key=lambda b: b.id)
    session.add(version)
    session.flush()
    _emit_version(session, "dataset_version.created", version, actor)
    return version


def delete_version(session: Session, actor: Principal, version_id: str) -> None:
    version = get_version(session, actor, version_id)
    actor.require_write()
    if version.eval_results:
        raise Conflict("This version has eval results. Delete them first.")
    used_by = session.scalars(
        select(DatasetVersion.id).where(DatasetVersion.baseline_version_id == version.id).limit(3)
    ).all()
    if used_by:
        raise Conflict(f"This version is the baseline of {', '.join(used_by)}.")
    _emit_version(session, "dataset_version.deleted", version, actor)
    session.delete(version)
    session.flush()


def manifest(session: Session, actor: Principal, version_id: str) -> schemas.Manifest:
    version = get_version(session, actor, version_id)
    files = [
        schemas.ManifestFile(
            batch_id=b.id,
            data_source_id=b.data_source_id,
            source_kind=b.allocation.data_source.kind,
            spec_version_id=b.spec_version_id,
            uri=a["uri"],
            format=a["format"],
            sha256=a.get("sha256"),
            size_bytes=a.get("size_bytes"),
            record_count=a.get("record_count"),
        )
        for b in version.batches
        for a in b.artifacts
    ]
    return schemas.Manifest(
        dataset_version_id=version.id,
        batch_count=len(version.batches),
        file_count=len(files),
        files=files,
    )


# --- eval results ----------------------------------------------------------------------------


def _emit_eval(session: Session, type: str, ev: EvalResult, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.EvalResult.model_validate(ev),
        subject_id=ev.id,
        project_id=ev.project_id,
        actor=actor,
    )


def list_evals(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    dataset_version_id: str | None,
    capability_id: str | None,
    metric: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[EvalResult], str | None]:
    where = []
    if dataset_version_id:
        where.append(EvalResult.dataset_version_id == dataset_version_id)
    if capability_id:
        where.append(EvalResult.capability_id == capability_id)
    if metric:
        where.append(EvalResult.metric == metric)
    return scoped.list_scoped(
        session, actor, EvalResult, project_id=project_id, limit=limit, cursor=cursor, where=where
    )


def get_eval(session: Session, actor: Principal, eval_id: str) -> EvalResult:
    return scoped.get_scoped(session, actor, EvalResult, eval_id, "eval result")


def record_eval(session: Session, actor: Principal, body: schemas.EvalResultCreate) -> EvalResult:
    actor.require_write()
    version = session.get(DatasetVersion, body.dataset_version_id)
    if version is None or not actor.can_see_project(version.project_id):
        raise Invalid(f"No dataset version with id '{body.dataset_version_id}'.")
    cap = version.dataset.capability
    metric = body.metric or cap.eval_metric
    higher_is_better = body.higher_is_better
    if higher_is_better is None:
        if metric != cap.eval_metric:
            raise Invalid(
                f"'{metric}' isn't the capability's main metric, so higher_is_better is required."
            )
        higher_is_better = cap.higher_is_better
    ev = EvalResult(
        id=new_id("evr"),
        project_id=version.project_id,
        dataset_version_id=version.id,
        capability_id=cap.id,
        metric=metric,
        value=body.value,
        higher_is_better=higher_is_better,
        run_name=body.run_name,
        external_run_url=body.external_run_url,
        recorded_at=body.recorded_at or utcnow(),
        notes=body.notes,
    )
    session.add(ev)
    session.flush()
    _emit_eval(session, "eval_result.recorded", ev, actor)
    return ev


def delete_eval(session: Session, actor: Principal, eval_id: str) -> None:
    ev = get_eval(session, actor, eval_id)
    actor.require_write()
    _emit_eval(session, "eval_result.deleted", ev, actor)
    session.delete(ev)
    session.flush()
