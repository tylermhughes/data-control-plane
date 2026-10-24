from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, InProject, ProjectScoped, utcnow
from app.models.batch import Batch
from app.models.capability import Capability

dataset_version_batches = Table(
    "dataset_version_batches",
    Base.metadata,
    Column(
        "dataset_version_id",
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("batch_id", ForeignKey("batches.id", ondelete="RESTRICT"), primary_key=True),
)


class Dataset(ProjectScoped, Base):
    """A named line of training data for one capability, e.g. "damage-det"."""

    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.id", ondelete="RESTRICT"), index=True
    )

    capability: Mapped[Capability] = relationship()
    versions: Mapped[list["DatasetVersion"]] = relationship(
        back_populates="dataset", order_by="DatasetVersion.version"
    )


class DatasetVersion(InProject, Base):
    """A frozen set of accepted batches, compared against a baseline version."""

    __tablename__ = "dataset_versions"
    __table_args__ = (UniqueConstraint("dataset_id", "version"),)

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="RESTRICT"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    baseline_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="RESTRICT"), index=True
    )
    notes: Mapped[str] = mapped_column(Text, default="")

    dataset: Mapped[Dataset] = relationship(back_populates="versions")
    baseline: Mapped["DatasetVersion | None"] = relationship(remote_side="DatasetVersion.id")
    batches: Mapped[list[Batch]] = relationship(
        secondary=dataset_version_batches, order_by="Batch.id"
    )
    eval_results: Mapped[list["EvalResult"]] = relationship(
        back_populates="dataset_version", order_by="EvalResult.id"
    )

    @property
    def capability_id(self) -> str:
        return self.dataset.capability_id

    @property
    def batch_ids(self) -> list[str]:
        return [b.id for b in self.batches]

    def new_batches(self) -> list[Batch]:
        """Batches in this version that its baseline didn't have."""
        old = set(self.baseline.batch_ids) if self.baseline else set()
        return [b for b in self.batches if b.id not in old]


class EvalResult(InProject, Base):
    """What a dataset version did to one metric, e.g. recall@0.5 = 0.857."""

    __tablename__ = "eval_results"

    dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="RESTRICT"), index=True
    )
    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.id", ondelete="RESTRICT"), index=True
    )
    metric: Mapped[str] = mapped_column(String(200))
    value: Mapped[float] = mapped_column(Float)
    higher_is_better: Mapped[bool] = mapped_column(Boolean)
    run_name: Mapped[str] = mapped_column(String(200), default="")
    external_run_url: Mapped[str | None] = mapped_column(String(2000))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    notes: Mapped[str] = mapped_column(Text, default="")

    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="eval_results")
