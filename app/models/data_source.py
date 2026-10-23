from datetime import date

from sqlalchemy import CheckConstraint, Date, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProjectScoped

KINDS = (
    "human_vendor",
    "expert_network",
    "synthetic",
    "rl_environment",
    "enterprise_workflow",
    "beta_users",
    "licensed_dataset",
)
LICENSE_TYPES = (
    "owned",
    "vendor_agreement",
    "licensed",
    "customer_terms",
    "employee_notice",
    "open_license",
    "other",
)


def _one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class DataSource(ProjectScoped, Base):
    """Where data comes from, with the rights terms it comes under."""

    __tablename__ = "data_sources"
    __table_args__ = (
        UniqueConstraint("project_id", "name"),
        CheckConstraint(_one_of("kind", KINDS), name="kind"),
        CheckConstraint(_one_of("license_type", LICENSE_TYPES), name="license_type"),
    )

    kind: Mapped[str] = mapped_column(String(32))
    default_unit: Mapped[str] = mapped_column(String(32))
    license_type: Mapped[str] = mapped_column(String(32))
    consent_scope: Mapped[str] = mapped_column(Text, default="")
    rights_expires_at: Mapped[date | None] = mapped_column(Date)
    pii_handling: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
