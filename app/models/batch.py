from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, InProject, utcnow
from app.models.quality import QualityRun
from app.models.request import Allocation
from app.models.spec import SpecVersion

BATCH_STATUSES = ("received", "checking", "passed", "failed", "accepted", "rejected")
UNDECIDED = frozenset({"received", "passed", "failed"})  # checking is "busy", not undecided


class Batch(InProject, Base):
    """One delivery against an allocation: what arrived, what was kept, and what it cost.

    Decisions come from DCP (someone accepts or rejects it here) or from outside (a vendor's
    QA or a labeling tool). External batches are identified by (data source, external_ref), so
    re-importing them updates the same batch instead of creating a duplicate.
    """

    __tablename__ = "batches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('received', 'checking', 'passed', 'failed', 'accepted', 'rejected')",
            name="status",
        ),
        CheckConstraint("decision_source IN ('dcp', 'external')", name="decision_source"),
        CheckConstraint("delivered_count >= 0", name="delivered_not_negative"),
        CheckConstraint(
            "accepted_count IS NULL OR (accepted_count >= 0 AND accepted_count <= delivered_count)",
            name="accepted_within_delivered",
        ),
        CheckConstraint("spend >= 0", name="spend_not_negative"),
        UniqueConstraint("data_source_id", "external_ref"),
    )

    allocation_id: Mapped[str] = mapped_column(
        ForeignKey("allocations.id", ondelete="RESTRICT"), index=True
    )
    data_source_id: Mapped[str] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    spec_version_id: Mapped[str] = mapped_column(
        ForeignKey("spec_versions.id", ondelete="RESTRICT"), index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(16), default="received")
    delivered_count: Mapped[int] = mapped_column(Integer)
    accepted_count: Mapped[int | None] = mapped_column(Integer)
    contributor_count: Mapped[int | None] = mapped_column(Integer)
    spend: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    currency: Mapped[str] = mapped_column(String(3))
    attribute_counts: Mapped[dict[str, dict[str, int]]] = mapped_column(JSONB, default=dict)
    # Values DCP can't measure from files (e.g. rater agreement), reported by the source.
    reported_metrics: Mapped[dict[str, float]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    override_reason: Mapped[str | None] = mapped_column(Text)
    # Filled in by DCP: delivered_count from the files' record count (when it wasn't given),
    # and spend estimated as quoted rate × delivered (when it wasn't given).
    delivered_count_from_files: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    spend_is_estimate: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    artifacts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    decision_source: Mapped[str | None] = mapped_column(String(16))
    decided_by: Mapped[str | None] = mapped_column(String(200))
    decided_by_key_id: Mapped[str | None] = mapped_column(String(40))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    external_ref: Mapped[str | None] = mapped_column(String(200))
    external_url: Mapped[str | None] = mapped_column(String(2000))

    allocation: Mapped[Allocation] = relationship(back_populates="batches")
    spec_version: Mapped[SpecVersion] = relationship()
    quality_runs: Mapped[list[QualityRun]] = relationship(
        order_by="QualityRun.id", passive_deletes=True
    )

    @property
    def latest_quality_run(self) -> QualityRun | None:
        return self.quality_runs[-1] if self.quality_runs else None

    @property
    def quality(self) -> dict[str, Any] | None:
        """The latest quality run in brief (the API's `quality` field)."""
        run = self.latest_quality_run
        if run is None:
            return None
        return {
            "run_id": run.id,
            "status": run.status,
            "failed_checks": [c["name"] for c in run.checks if c["outcome"] == "failed"],
            "warnings": [c["name"] for c in run.checks if c["outcome"] == "warning"],
            "finished_at": run.finished_at,
        }

    @property
    def request_id(self) -> str:
        return self.allocation.request_id

    @property
    def rejected_count(self) -> int | None:
        if self.accepted_count is None:
            return None
        return self.delivered_count - self.accepted_count
