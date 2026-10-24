from decimal import Decimal

from sqlalchemy import Boolean, Float, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProjectScoped


class Capability(ProjectScoped, Base):
    """Something the data should improve, measured by one main eval metric."""

    __tablename__ = "capabilities"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    eval_metric: Mapped[str] = mapped_column(String(200))
    higher_is_better: Mapped[bool] = mapped_column(Boolean)
    value_per_point: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    # How much of the metric counts as one "point" (0.01 = one percentage point of a 0-1 metric).
    point_size: Mapped[float] = mapped_column(Float, default=1.0, server_default=text("1"))
    currency: Mapped[str] = mapped_column(String(3))
