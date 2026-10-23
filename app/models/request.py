from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, InProject
from app.models.data_source import DataSource
from app.models.spec import SpecVersion

if TYPE_CHECKING:
    from app.models.batch import Batch

PRIORITIES = ("P0", "P1", "P2", "P3")
REQUEST_STATUSES = ("draft", "open", "closed", "cancelled")
ALLOCATION_STATUSES = ("planned", "active", "complete", "cancelled")


def _one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Request(InProject, Base):
    """An ask for data to improve one capability. Split into allocations across sources."""

    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint(_one_of("priority", PRIORITIES), name="priority"),
        CheckConstraint(_one_of("status", REQUEST_STATUSES), name="status"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    requested_by: Mapped[str] = mapped_column(String(200), default="")
    priority: Mapped[str] = mapped_column(String(2), default="P2")
    rationale: Mapped[str] = mapped_column(Text, default="")
    target_metric: Mapped[str] = mapped_column(String(200), default="")
    quantity: Mapped[int] = mapped_column(Integer)
    unit: Mapped[str] = mapped_column(String(32))
    due_date: Mapped[date | None] = mapped_column(Date)
    spec_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("spec_versions.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="draft")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    spec_version: Mapped[SpecVersion | None] = relationship()
    allocations: Mapped[list["Allocation"]] = relationship(
        back_populates="request", order_by="Allocation.id"
    )


class Allocation(InProject, Base):
    """Part of a request given to one source: quantity, quoted rate, due date.

    Pins the spec version it was quoted against, so later spec changes never rewrite history.
    """

    __tablename__ = "allocations"
    __table_args__ = (
        CheckConstraint(_one_of("status", ALLOCATION_STATUSES), name="status"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("quoted_unit_rate >= 0", name="rate_not_negative"),
    )

    request_id: Mapped[str] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"), index=True
    )
    data_source_id: Mapped[str] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    spec_version_id: Mapped[str] = mapped_column(
        ForeignKey("spec_versions.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer)
    unit: Mapped[str] = mapped_column(String(32))
    quoted_unit_rate: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    currency: Mapped[str] = mapped_column(String(3))
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="planned")
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    request: Mapped[Request] = relationship(back_populates="allocations")
    data_source: Mapped[DataSource] = relationship()
    spec_version: Mapped[SpecVersion] = relationship()
    batches: Mapped[list["Batch"]] = relationship(back_populates="allocation", order_by="Batch.id")

    @property
    def quoted_cost(self) -> Decimal:
        return self.quoted_unit_rate * self.quantity

    # Delivery totals, from this allocation's batches.
    @property
    def batch_count(self) -> int:
        return len(self.batches)

    @property
    def delivered_count(self) -> int:
        return sum(b.delivered_count for b in self.batches)

    @property
    def accepted_count(self) -> int:
        return sum(b.accepted_count or 0 for b in self.batches if b.status == "accepted")

    @property
    def spend(self) -> Decimal:
        return sum((b.spend for b in self.batches), Decimal(0))

    @property
    def progress(self) -> float:
        """Accepted units as a share of the allocated quantity (can exceed 1)."""
        return round(self.accepted_count / self.quantity, 4)
