from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, MetaData, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Predictable constraint names, so migrations can refer to them later.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class InProject(Timestamped):
    """Columns shared by everything that lives inside a project."""

    id: Mapped[str] = mapped_column(String(40), primary_key=True)

    @declared_attr
    def project_id(cls) -> Mapped[str]:
        # RESTRICT: a project can't be deleted while things still live in it.
        return mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)


class ProjectScoped(InProject):
    """Named things inside a project. Names are unique per project."""

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
