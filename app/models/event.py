from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Event(Base):
    """Append-only record of every change. Feeds outbound webhooks (M4b) and the audit trail.

    No foreign keys on purpose: events must outlive the things they describe.
    """

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_undispatched", "id", postgresql_where=text("dispatched_at IS NULL")),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    subject_id: Mapped[str] = mapped_column(String(40), index=True)
    project_id: Mapped[str | None] = mapped_column(String(40), index=True)
    actor_key_id: Mapped[str | None] = mapped_column(String(40))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Set once the worker has queued this event for every matching webhook endpoint.
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
