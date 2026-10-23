from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProjectScoped, Timestamped


class Spec(ProjectScoped, Base):
    """What data must look like. The content lives in its numbered versions."""

    __tablename__ = "specs"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    versions: Mapped[list["SpecVersion"]] = relationship(
        back_populates="spec",
        order_by="SpecVersion.version",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SpecVersion(Timestamped, Base):
    """One version of a spec. Drafts can be edited; approved versions never change."""

    __tablename__ = "spec_versions"
    __table_args__ = (
        UniqueConstraint("spec_id", "version"),
        CheckConstraint("status IN ('draft', 'approved')", name="status"),
        # At most one draft per spec.
        Index(
            "uq_spec_versions_one_draft",
            "spec_id",
            unique=True,
            postgresql_where=text("status = 'draft'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    spec_id: Mapped[str] = mapped_column(ForeignKey("specs.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    guidelines: Mapped[str] = mapped_column(Text, default="")
    attributes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    coverage_targets: Mapped[dict[str, dict[str, float]]] = mapped_column(JSONB, default=dict)
    acceptance_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    record_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    change_note: Mapped[str] = mapped_column(Text, default="")
    approved_by: Mapped[str | None] = mapped_column(String(200))
    approved_by_key_id: Mapped[str | None] = mapped_column(String(40))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    spec: Mapped[Spec] = relationship(back_populates="versions")
