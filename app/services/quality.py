"""Quality runs: queue the automated checks on a batch, run them, and move the batch on.

Undecided batches go checking -> passed/failed, and a person then accepts or rejects them.
Batches already decided (in DCP or outside it) keep their decision; the run only adds
findings, as decided in M4a.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.checks import runner
from app.errors import Conflict
from app.ids import new_id
from app.models import Batch, QualityRun
from app.models.base import utcnow
from app.schemas import batches as batch_schemas
from app.schemas import quality as schemas
from app.services import events, jobs, scoped
from app.services.principal import CLI, Principal

JOB_TYPE = "quality_check"


def _emit_run(session: Session, run: QualityRun, actor: Principal) -> None:
    events.emit(
        session,
        "quality.completed",
        schemas.QualityRun.model_validate(run),
        subject_id=run.id,
        project_id=run.project_id,
        actor=actor,
    )


def queue_checks(session: Session, batch: Batch, *, trigger: str) -> QualityRun:
    """Queue a run (in the caller's transaction). Undecided batches move to `checking`."""
    run = QualityRun(
        id=new_id("qrn"), project_id=batch.project_id, batch_id=batch.id, trigger=trigger
    )
    session.add(run)
    session.flush()
    jobs.enqueue(session, JOB_TYPE, {"run_id": run.id})
    if batch.status in ("received", "passed", "failed"):
        batch.status = "checking"
    session.refresh(batch, ["quality_runs"])
    return run


def request_checks(session: Session, actor: Principal, batch_id: str) -> QualityRun:
    from app.services import batches  # avoid a circular import at module load

    batch = batches.get_batch(session, actor, batch_id)
    actor.require_write()
    if batch.status == "checking":
        raise Conflict("Checks are already running on this batch.")
    if not batch.artifacts:
        raise Conflict("This batch lists no files, so there is nothing to check.")
    return queue_checks(session, batch, trigger="manual")


def run_job(session: Session, payload: dict[str, Any]) -> None:
    run = session.get_one(QualityRun, payload["run_id"])
    run.status, run.started_at = "running", utcnow()
    session.commit()
    try:
        runner.execute(session, run)
    except Exception as exc:  # a broken check must not leave the batch stuck in `checking`
        session.rollback()
        run = session.get_one(QualityRun, payload["run_id"])
        run.status, run.error = "error", f"{exc.__class__.__name__}: {exc}"
    _finish(session, run)


def run_failed(session: Session, payload: dict[str, Any], error: str) -> None:
    """The job itself kept crashing (e.g. the database was unreachable)."""
    run = session.get_one(QualityRun, payload["run_id"])
    run.status, run.error = "error", error
    _finish(session, run)


def _finish(session: Session, run: QualityRun) -> None:
    run.finished_at = utcnow()
    batch = session.get_one(Batch, run.batch_id)
    if batch.status == "checking":
        batch.status = "passed" if run.status == "passed" else "failed"
    if batch.status in ("passed", "failed"):  # undecided: DCP may still fill figures in
        if batch.delivered_count_from_files and "record_count" in run.metrics:
            batch.delivered_count = run.metrics["record_count"]
        if batch.spend_is_estimate:
            batch.spend = batch.allocation.quoted_unit_rate * batch.delivered_count
    session.flush()
    _emit_run(session, run, CLI)
    events.emit(
        session,
        "batch.checked",
        batch_schemas.Batch.model_validate(batch),
        subject_id=batch.id,
        project_id=batch.project_id,
        actor=CLI,
    )
    session.commit()


jobs.register(JOB_TYPE, run_job, run_failed)


def list_runs(
    session: Session, actor: Principal, batch_id: str, *, limit: int, cursor: str | None
) -> tuple[Sequence[QualityRun], str | None]:
    from app.services import batches

    batches.get_batch(session, actor, batch_id)
    return scoped.list_scoped(
        session,
        actor,
        QualityRun,
        project_id=None,
        limit=limit,
        cursor=cursor,
        where=[QualityRun.batch_id == batch_id],
    )


def get_run(session: Session, actor: Principal, run_id: str) -> QualityRun:
    return scoped.get_scoped(session, actor, QualityRun, run_id, "quality run")


def latest_finished(batch: Batch) -> QualityRun | None:
    finished = [r for r in batch.quality_runs if r.status in ("passed", "failed")]
    return finished[-1] if finished else None
