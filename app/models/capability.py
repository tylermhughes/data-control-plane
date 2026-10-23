from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProjectScoped


class Capability(ProjectScoped, Base):
    """Something the data should improve, measured by one main eval metric."""

    __tablename__ = "capabilities"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    eval_metric: Mapped[str] = mapped_column(String(200))
    higher_is_better: Mapped[bool] = mapped_column(Boolean)
    value_per_point: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    currency: Mapped[str] = mapped_column(String(3))
