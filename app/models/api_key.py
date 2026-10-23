from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped


class ApiKey(Timestamped, Base):
    """An API key. Only a SHA-256 hash of the secret is stored, never the secret itself."""

    __tablename__ = "api_keys"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'project')", name="role"),
        CheckConstraint("access IN ('read', 'write')", name="access"),
        CheckConstraint(
            "(role = 'admin' AND project_id IS NULL) "
            "OR (role = 'project' AND project_id IS NOT NULL)",
            name="project_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    key_prefix: Mapped[str] = mapped_column(String(16))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(16))
    access: Mapped[str] = mapped_column(String(8))
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
