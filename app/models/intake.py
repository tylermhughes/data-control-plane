"""Automatic intake of deliveries: inbound webhooks and bucket-watching connectors."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
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
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, InProject, Timestamped, utcnow


class InboundEndpoint(InProject, Base):
    """A URL a source's own systems POST signed delivery messages to.

    Its signing secret is derived from DCP_SECRET_KEY, like outbound webhook secrets.
    """

    __tablename__ = "inbound_endpoints"

    data_source_id: Mapped[str] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    description: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    secret_version: Mapped[int] = mapped_column(Integer, default=1)
    secret_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def url_path(self) -> str:
        return f"/v1/inbound/{self.id}"


class InboundMessage(Base):
    """Every message received on an inbound endpoint, processed or rejected."""

    __tablename__ = "inbound_messages"
    __table_args__ = (
        CheckConstraint("status IN ('processed', 'rejected')", name="status"),
        # A message id is processed at most once per endpoint; rejected attempts are all kept.
        Index(
            "uq_inbound_messages_processed",
            "endpoint_id",
            "message_id",
            unique=True,
            postgresql_where=text("status = 'processed'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    endpoint_id: Mapped[str] = mapped_column(
        ForeignKey("inbound_endpoints.id", ondelete="CASCADE"), index=True
    )
    message_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16))
    http_status: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    batch_id: Mapped[str | None] = mapped_column(String(40))
    message_type: Mapped[str | None] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Connector(InProject, Base):
    """Watches a bucket folder and turns each new file into a batch for its data source."""

    __tablename__ = "connectors"
    __table_args__ = (
        CheckConstraint("type IN ('s3_watch')", name="type"),
        CheckConstraint("poll_interval_seconds >= 15", name="poll_interval"),
        Index("ix_connectors_due", "next_poll_at", postgresql_where=text("enabled")),
    )

    data_source_id: Mapped[str] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    type: Mapped[str] = mapped_column(String(32), default="s3_watch")
    description: Mapped[str] = mapped_column(Text, default="")
    bucket: Mapped[str] = mapped_column(String(255))
    prefix: Mapped[str] = mapped_column(String(1024), default="")
    endpoint_url: Mapped[str | None] = mapped_column(String(2000))
    region: Mapped[str | None] = mapped_column(String(64))
    allocation_id: Mapped[str | None] = mapped_column(
        ForeignKey("allocations.id", ondelete="RESTRICT")
    )
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    credentials_encrypted: Mapped[str | None] = mapped_column(Text)
    access_key_hint: Mapped[str | None] = mapped_column(String(16))
    next_poll_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_found_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    @property
    def has_credentials(self) -> bool:
        return self.credentials_encrypted is not None


class ConnectorObject(Timestamped, Base):
    """A file a connector has seen, and the batch it became."""

    __tablename__ = "connector_objects"

    connector_id: Mapped[str] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(1024), primary_key=True)
    etag: Mapped[str] = mapped_column(String(200), default="")
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    last_modified: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    batch_id: Mapped[str | None] = mapped_column(String(40))
    error: Mapped[str | None] = mapped_column(Text)

    def same_version(self, other: dict[str, Any]) -> bool:
        return bool(
            self.etag == other["etag"]
            and self.size_bytes == other["size_bytes"]
            and self.last_modified == other["last_modified"]
        )
