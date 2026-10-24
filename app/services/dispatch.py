"""The worker side of webhooks: queue each event for matching endpoints, then send.

1. dispatch_events: every event not yet dispatched gets one delivery per matching endpoint
   (disabled endpoints too: their messages wait until they're enabled again). Events are
   picked up by a "not dispatched yet" marker, not by position, so an event whose
   transaction commits late is never skipped.
2. send_due: claims due deliveries (safe with several workers), signs and POSTs each one,
   and records the attempt. Failures retry with growing gaps for about a day, then fail.
"""

import errno
import json
import logging
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.ids import new_id
from app.models import Event, IdempotencyRecord, WebhookDelivery, WebhookEndpoint
from app.models.base import utcnow
from app.services import signing, urls
from app.services.webhooks import ROTATION_OVERLAP

logger = logging.getLogger(__name__)

# Gaps before each retry: about a day in total over 8 attempts.
BACKOFF = (
    timedelta(seconds=5),
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
    timedelta(hours=5),
    timedelta(hours=10),
    timedelta(hours=10),
)
MAX_ATTEMPTS = len(BACKOFF) + 1
CLAIM_LEASE = timedelta(minutes=2)  # a claimed delivery is retried if the worker dies
RESPONSE_PREVIEW = 1000
IDEMPOTENCY_TTL = timedelta(hours=24)


def matches(patterns: list[str], event_type: str) -> bool:
    for pattern in patterns:
        if pattern == "*" or pattern == event_type:
            return True
        if pattern.endswith(".*") and event_type.startswith(pattern[:-1]):
            return True
    return False


def payload_for(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "type": event.type,
        "timestamp": event.created_at.isoformat(),
        "project_id": event.project_id,
        "subject_id": event.subject_id,
        "data": event.data,
    }


def dispatch_events(session: Session, *, limit: int = 500, now: datetime | None = None) -> int:
    now = now or utcnow()
    batch = session.scalars(
        select(Event)
        .where(Event.dispatched_at.is_(None))
        .order_by(Event.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    ).all()
    if not batch:
        return 0
    endpoints = session.scalars(select(WebhookEndpoint)).all()
    for event in batch:
        for ep in endpoints:
            if ep.project_id not in (None, event.project_id):
                continue
            if not matches(ep.event_types, event.type):
                continue
            session.add(
                WebhookDelivery(
                    id=new_id("dlv"),
                    endpoint_id=ep.id,
                    project_id=event.project_id,
                    event_id=event.id,
                    event_type=event.type,
                    payload=payload_for(event),
                    next_attempt_at=now,
                )
            )
        event.dispatched_at = now
    session.commit()
    return len(batch)


def claim_due(session: Session, *, limit: int = 50, now: datetime | None = None) -> list[str]:
    now = now or utcnow()
    ids = list(
        session.scalars(
            select(WebhookDelivery.id)
            .join(WebhookEndpoint, WebhookEndpoint.id == WebhookDelivery.endpoint_id)
            .where(
                WebhookDelivery.status == "pending",
                WebhookDelivery.next_attempt_at <= now,
                WebhookEndpoint.enabled.is_(True),
            )
            .order_by(WebhookDelivery.next_attempt_at)
            .limit(limit)
            .with_for_update(of=WebhookDelivery, skip_locked=True)
        ).all()
    )
    if ids:
        session.execute(
            update(WebhookDelivery)
            .where(WebhookDelivery.id.in_(ids))
            .values(next_attempt_at=now + CLAIM_LEASE)
        )
    session.commit()
    return ids


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """A redirect counts as a failure: it could point somewhere the URL check didn't allow."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


_opener = urllib.request.build_opener(_NoRedirects)


def _post(url: str, body: bytes, headers: dict[str, str]) -> tuple[int | None, str, str | None]:
    """Returns (status code, response preview, error)."""
    try:
        urls.check_webhook_url(url)  # http/https only, re-checked at every send
        urls.check_resolved(url)
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310
        with _opener.open(request, timeout=get_settings().webhook_timeout_seconds) as response:
            preview = response.read(RESPONSE_PREVIEW).decode(errors="replace")
            return int(response.status), preview, None
    except urllib.error.HTTPError as exc:
        preview = exc.read(RESPONSE_PREVIEW).decode(errors="replace") if exc.fp else ""
        return exc.code, preview, None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        return None, "", describe_error(url, reason)


def describe_error(url: str, reason: object) -> str:
    """A useful error message for the delivery log.

    When IPv6 is unreachable (common inside Docker), Python reports that first error even if
    IPv4 was also tried, hiding the real cause. In that case, report what IPv4 says instead.
    """
    if isinstance(reason, OSError) and reason.errno == errno.ENETUNREACH:
        parts = urlsplit(url)
        port = parts.port or (443 if parts.scheme == "https" else 80)
        try:
            infos = socket.getaddrinfo(parts.hostname, port, socket.AF_INET, socket.SOCK_STREAM)
            with socket.create_connection((str(infos[0][4][0]), port), timeout=2):
                pass
        except OSError as ipv4_error:
            return ipv4_error.strerror or str(ipv4_error)
    return str(reason) or reason.__class__.__name__


def signature_header(
    ep: WebhookEndpoint, message_id: str, timestamp: int, body: bytes, now: datetime
) -> str:
    versions = [ep.secret_version]
    rotated = ep.secret_rotated_at
    if rotated and ep.secret_version > 1 and now - rotated < ROTATION_OVERLAP:
        versions.append(ep.secret_version - 1)
    return " ".join(
        signing.sign(signing.endpoint_secret(ep.id, v), message_id, timestamp, body)
        for v in versions
    )


def send_one(
    session: Session,
    delivery_id: str,
    *,
    now: datetime | None = None,
    post: Callable[[str, bytes, dict[str, str]], tuple[int | None, str, str | None]] = _post,
) -> str:
    """Send one delivery and record the attempt. Returns the delivery's new status."""
    now = now or utcnow()
    delivery = session.get_one(WebhookDelivery, delivery_id)
    ep = delivery.endpoint
    body = json.dumps(delivery.payload, separators=(",", ":"), sort_keys=True).encode()
    timestamp = int(now.timestamp())
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DataControlPlane-Webhooks/0.1",
        "webhook-id": delivery.event_id,
        "webhook-timestamp": str(timestamp),
        "webhook-signature": signature_header(ep, delivery.event_id, timestamp, body, now),
    }

    started = time.monotonic()
    status_code, preview, error = post(ep.url, body, headers)
    duration_ms = int((time.monotonic() - started) * 1000)

    delivery.attempt_count += 1
    delivery.attempts = [
        *delivery.attempts,
        {
            "at": now.isoformat(),
            "status_code": status_code,
            "error": error,
            "duration_ms": duration_ms,
            "response_body": preview,
        },
    ]
    if status_code is not None and 200 <= status_code < 300:
        delivery.status, delivery.delivered_at = "delivered", now
        ep.last_success_at = now
    else:
        ep.last_failure_at = now
        ep.last_failure_reason = error or f"HTTP {status_code}"
        if delivery.attempt_count >= MAX_ATTEMPTS:
            delivery.status = "failed"
        else:
            delivery.next_attempt_at = now + BACKOFF[delivery.attempt_count - 1]
    session.commit()
    return delivery.status


def send_due(session: Session, *, limit: int = 50, now: datetime | None = None) -> int:
    ids = claim_due(session, limit=limit, now=now)
    for delivery_id in ids:
        try:
            send_one(session, delivery_id, now=now)
        except Exception:  # one broken delivery must not stop the others
            session.rollback()
            logger.exception("webhook delivery %s crashed; it will be retried", delivery_id)
    return len(ids)


def clean_up(session: Session, *, now: datetime | None = None) -> None:
    """Housekeeping: forget saved Idempotency-Key responses after 24 hours."""
    cutoff = (now or utcnow()) - IDEMPOTENCY_TTL
    session.execute(delete(IdempotencyRecord).where(IdempotencyRecord.created_at < cutoff))
    session.commit()
