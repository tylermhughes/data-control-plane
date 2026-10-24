from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.models import Job
from app.models.base import utcnow
from app.services import jobs


def test_jobs_run_once_and_failures_retry_then_give_up(db: Session) -> None:
    calls: list[dict[str, Any]] = []
    failures: list[str] = []

    def flaky(session: Session, payload: dict[str, Any]) -> None:
        calls.append(payload)
        raise RuntimeError("database hiccup")

    jobs.register("test.flaky", flaky, lambda s, p, error: failures.append(error))
    job = jobs.enqueue(db, "test.flaky", {"n": 1})
    db.commit()

    now = utcnow()
    for attempt, gap in enumerate(jobs.RETRY_AFTER, start=1):
        assert jobs.run_due(db, now=now) == 1
        db.refresh(job)
        assert (job.status, job.attempts) == ("queued", attempt)
        assert jobs.run_due(db, now=now) == 0  # not due yet
        now = job.run_after + timedelta(seconds=1)
        assert gap  # documented backoff
    assert jobs.run_due(db, now=now) == 1
    db.refresh(job)
    assert (job.status, job.attempts) == ("failed", jobs.MAX_ATTEMPTS)
    assert "database hiccup" in (job.last_error or "")
    assert len(calls) == jobs.MAX_ATTEMPTS
    assert failures == [job.last_error]


def test_successful_job_is_done(db: Session) -> None:
    seen: list[int] = []
    jobs.register("test.ok", lambda session, payload: seen.append(payload["n"]))
    jobs.enqueue(db, "test.ok", {"n": 7})
    db.commit()
    assert jobs.run_due(db) == 1
    assert seen == [7]
    assert db.query(Job).filter(Job.type == "test.ok").one().status == "done"


@pytest.fixture(autouse=True)
def _forget_test_handlers() -> Any:
    yield
    for name in ("test.flaky", "test.ok"):
        jobs._handlers.pop(name, None)
