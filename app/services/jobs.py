"""A small job queue in Postgres for background work (no Redis needed).

Jobs are claimed with FOR UPDATE SKIP LOCKED, so several workers never run the same job, and
a claim holds a job for 30 minutes so a crashed worker's job runs again later. A job that
raises is retried twice more (1 and 5 minutes later), then marked failed.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ids import new_id
from app.models import Job
from app.models.base import utcnow

logger = logging.getLogger(__name__)

CLAIM_LEASE = timedelta(minutes=30)
RETRY_AFTER = (timedelta(minutes=1), timedelta(minutes=5))
MAX_ATTEMPTS = len(RETRY_AFTER) + 1

Handler = Callable[[Session, dict[str, Any]], None]
FailureHandler = Callable[[Session, dict[str, Any], str], None]
_handlers: dict[str, tuple[Handler, FailureHandler | None]] = {}


def register(job_type: str, handler: Handler, on_failure: FailureHandler | None = None) -> None:
    _handlers[job_type] = (handler, on_failure)


def enqueue(session: Session, job_type: str, payload: dict[str, Any]) -> Job:
    """Add a job in the caller's transaction: it only exists if the caller's change commits."""
    job = Job(id=new_id("job"), type=job_type, payload=payload, run_after=utcnow())
    session.add(job)
    return job


def run_due(session: Session, *, limit: int = 1, now: datetime | None = None) -> int:
    """Claim and run up to `limit` due jobs. Returns how many ran."""
    ran = 0
    for _ in range(limit):
        current = now or utcnow()
        job = session.scalars(
            select(Job)
            .where(Job.status == "queued", Job.run_after <= current)
            .order_by(Job.run_after)
            .limit(1)
            .with_for_update(skip_locked=True)
        ).first()
        if job is None:
            break
        job.attempts += 1
        job.run_after = current + CLAIM_LEASE
        session.commit()
        _run(session, job.id)
        ran += 1
    return ran


def _run(session: Session, job_id: str) -> None:
    job = session.get_one(Job, job_id)
    handler, on_failure = _handlers[job.type]
    try:
        handler(session, job.payload)
    except Exception as exc:
        session.rollback()
        job = session.get_one(Job, job_id)
        job.last_error = f"{exc.__class__.__name__}: {exc}"
        logger.exception("job %s (%s) failed on attempt %d", job.id, job.type, job.attempts)
        if job.attempts >= MAX_ATTEMPTS:
            job.status = "failed"
            if on_failure:
                on_failure(session, job.payload, job.last_error)
        else:
            job.run_after = utcnow() + RETRY_AFTER[job.attempts - 1]
        session.commit()
        return
    job = session.get_one(Job, job_id)
    job.status = "done"
    session.commit()
