from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamped, utcnow


class WebhookEndpoint(Timestamped, Base):
    """A URL that receives signed event messages.

    project_id set: only that project's events. Null: every project's events (org-wide).
    The signing secret is never stored: it is derived from DCP_SECRET_KEY, the endpoint id
    and secret_version (see app.services.signing).
    """

    __tablename__ = "webhook_endpoints"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    url: Mapped[str] = mapped_column(String(2000))
    description: Mapped[str] = mapped_column(Text, default="")
    event_types: Mapped[list[str]] = mapped_column(JSONB, default=lambda: ["*"])
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    secret_version: Mapped[int] = mapped_column(Integer, default=1)
    secret_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_reason: Mapped[str | None] = mapped_column(Text)


class WebhookDelivery(Timestamped, Base):
    """One message to one endpoint, with every attempt to send it."""

    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'delivered', 'failed')", name="status"),
        Index(
            "ix_webhook_deliveries_due",
            "next_attempt_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    endpoint_id: Mapped[str] = mapped_column(
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str | None] = mapped_column(String(40), index=True)
    event_id: Mapped[str] = mapped_column(String(40), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    redelivery_of: Mapped[str | None] = mapped_column(String(40))

    endpoint: Mapped[WebhookEndpoint] = relationship()
