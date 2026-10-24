from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, InProject, Timestamped, utcnow


class Job(Timestamped, Base):
    """A unit of background work for the worker (e.g. run quality checks on a batch)."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("status IN ('queued', 'done', 'failed')", name="status"),
        Index("ix_jobs_due", "run_after", postgresql_where=text("status = 'queued'")),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_error: Mapped[str | None] = mapped_column(Text)


class QualityRun(InProject, Base):
    """One run of the automated checks on a batch's files."""

    __tablename__ = "quality_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'passed', 'failed', 'error')", name="status"
        ),
    )

    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="queued")
    trigger: Mapped[str] = mapped_column(String(16), default="auto")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    attribute_counts: Mapped[dict[str, dict[str, int]]] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class RecordFingerprint(Base):
    """A 64-bit fingerprint of one record, for finding duplicates across a project."""

    __tablename__ = "record_fingerprints"
    __table_args__ = (Index("ix_record_fingerprints_lookup", "project_id", "fingerprint"),)

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), primary_key=True
    )
    fingerprint: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[str] = mapped_column(String(40))
