"""The worker side: queueing, signing, sending, retrying. Uses a real local HTTP receiver."""

import errno
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IdempotencyRecord, WebhookDelivery
from app.models.base import utcnow
from app.services import dispatch, signing
from app.worker.__main__ import run_once
from tests.helpers import Headers, new_project, post_ok
from tests.receiver import running_receiver


def endpoint(client: TestClient, admin: Headers, url: str, **extra: Any) -> Any:
    return post_ok(client, "/v1/webhook-endpoints", admin, {"url": url, **extra})


def deliveries(db: Session) -> list[WebhookDelivery]:
    db.expire_all()
    return list(db.scalars(select(WebhookDelivery).order_by(WebhookDelivery.id)))


def test_change_is_delivered_signed(client: TestClient, admin: Headers, db: Session) -> None:
    with running_receiver() as rx:
        ep = endpoint(client, admin, rx.url, event_types=["project.created"])
        project_id = new_project(client, admin, "Vision")
        run_once(db)

        assert len(rx.received) == 1
        msg = rx.received[0]
        assert msg.json["type"] == "project.created"
        assert msg.json["subject_id"] == project_id
        assert msg.json["data"]["name"] == "Vision"
        assert msg.headers["webhook-id"] == msg.json["id"]
        assert signing.verify(
            ep["secret"],
            msg.headers["webhook-id"],
            int(msg.headers["webhook-timestamp"]),
            msg.body,
            msg.headers["webhook-signature"],
        )

    [d] = deliveries(db)
    assert (d.status, d.attempt_count, d.attempts[0]["status_code"]) == ("delivered", 1, 200)
    got = client.get(f"/v1/webhook-endpoints/{ep['id']}", headers=admin).json()
    assert got["last_success_at"] is not None


def test_routing_by_project_and_event_type(client: TestClient, admin: Headers, db: Session) -> None:
    a = new_project(client, admin, "A")
    b = new_project(client, admin, "B")
    with running_receiver() as rx:
        org_wide = endpoint(client, admin, rx.url, event_types=["capability.*"])
        only_a = endpoint(client, admin, rx.url, project_id=a, event_types=["*"])
        run_once(db)  # endpoint creation events themselves
        rx.received.clear()
        for project in (a, b):
            post_ok(
                client,
                "/v1/capabilities",
                admin,
                {
                    "project_id": project,
                    "name": "Damage",
                    "eval_metric": "recall",
                    "value_per_point": "1",
                    "currency": "USD",
                },
            )
        run_once(db)

    by_endpoint: dict[str, list[str]] = {}
    for d in deliveries(db):
        if d.event_type == "capability.created":
            by_endpoint.setdefault(d.endpoint_id, []).append(d.project_id or "")
    assert sorted(by_endpoint[org_wide["id"]]) == sorted([a, b])
    assert by_endpoint[only_a["id"]] == [a]
    assert len(rx.received) == 3


def test_failures_retry_with_backoff_then_fail(
    client: TestClient, admin: Headers, db: Session
) -> None:
    with running_receiver() as rx:
        rx.status = 503
        ep = endpoint(client, admin, rx.url, event_types=["project.created"])
        new_project(client, admin)
        now = utcnow()
        dispatch.dispatch_events(db, now=now)
        [d] = deliveries(db)

        for attempt, gap in enumerate(dispatch.BACKOFF, start=1):
            assert dispatch.send_one(db, d.id, now=now) == "pending"
            db.refresh(d)
            assert d.attempt_count == attempt
            assert d.next_attempt_at == now + gap
            assert dispatch.claim_due(db, now=now + gap - timedelta(seconds=1)) == []
            now += gap
        assert dispatch.send_one(db, d.id, now=now) == "failed"

    db.refresh(d)
    assert d.attempt_count == dispatch.MAX_ATTEMPTS
    assert [a["status_code"] for a in d.attempts] == [503] * dispatch.MAX_ATTEMPTS
    assert sum(dispatch.BACKOFF, timedelta()) > timedelta(hours=24)
    health = client.get(f"/v1/webhook-endpoints/{ep['id']}", headers=admin).json()
    assert health["last_failure_reason"] == "HTTP 503"


def test_unreachable_receiver_records_the_error(
    client: TestClient, admin: Headers, db: Session
) -> None:
    endpoint(client, admin, "http://127.0.0.1:9/nothing-here", event_types=["project.created"])
    new_project(client, admin)
    run_once(db)
    [d] = deliveries(db)
    assert d.status == "pending"
    assert d.attempts[0]["status_code"] is None
    assert d.attempts[0]["error"]


def test_redirects_count_as_failures(client: TestClient, admin: Headers, db: Session) -> None:
    with running_receiver() as rx:
        rx.redirect_to = "http://169.254.169.254/latest/meta-data/"
        endpoint(client, admin, rx.url, event_types=["project.created"])
        new_project(client, admin)
        run_once(db)
    [d] = deliveries(db)
    assert (d.status, d.attempts[0]["status_code"]) == ("pending", 302)
    assert len(rx.received) == 1  # the redirect target was never contacted


def test_paused_endpoints_hold_messages_until_enabled(
    client: TestClient, admin: Headers, db: Session
) -> None:
    with running_receiver() as rx:
        ep = endpoint(client, admin, rx.url, event_types=["project.created"], enabled=False)
        new_project(client, admin)
        run_once(db)
        assert rx.received == []
        assert deliveries(db)[0].status == "pending"

        client.patch(f"/v1/webhook-endpoints/{ep['id']}", headers=admin, json={"enabled": True})
        run_once(db)
        assert len(rx.received) == 1


def test_rotated_secret_overlap(client: TestClient, admin: Headers, db: Session) -> None:
    with running_receiver() as rx:
        ep = endpoint(client, admin, rx.url, event_types=["project.created"])
        new = client.post(f"/v1/webhook-endpoints/{ep['id']}/rotate-secret", headers=admin).json()
        new_project(client, admin)
        run_once(db)
        msg = rx.received[0]
        args = (msg.headers["webhook-id"], int(msg.headers["webhook-timestamp"]), msg.body)
        header = msg.headers["webhook-signature"]
        assert len(header.split()) == 2
        assert signing.verify(new["secret"], *args, header)
        assert signing.verify(ep["secret"], *args, header)  # old secret still works for 24h

        later = utcnow() + timedelta(hours=25)
        stored = db.get_one(WebhookDelivery, deliveries(db)[0].id).endpoint
        single = dispatch.signature_header(stored, "evt_x", 1, b"{}", later)
        assert len(single.split()) == 1


def test_test_message_and_redelivery(client: TestClient, admin: Headers, db: Session) -> None:
    with running_receiver() as rx:
        ep = endpoint(client, admin, rx.url, event_types=["nothing.*"])
        queued = client.post(f"/v1/webhook-endpoints/{ep['id']}/test", headers=admin)
        assert queued.status_code == 202
        run_once(db)
        assert [m.json["type"] for m in rx.received] == ["webhook.test"]

        done = client.get(f"/v1/webhook-deliveries/{queued.json()['id']}", headers=admin).json()
        assert done["status"] == "delivered"
        assert done["next_attempt_at"] is None

        again = client.post(f"/v1/webhook-deliveries/{done['id']}/redeliver", headers=admin)
        assert again.json()["redelivery_of"] == done["id"]
        run_once(db)
        assert len(rx.received) == 2
        assert rx.received[0].headers["webhook-id"] == rx.received[1].headers["webhook-id"]


def test_events_from_before_an_endpoint_existed_are_not_sent(
    client: TestClient, admin: Headers, db: Session
) -> None:
    new_project(client, admin, "Early")
    run_once(db)  # dispatched with no endpoints
    with running_receiver() as rx:
        endpoint(client, admin, rx.url, event_types=["project.created"])
        run_once(db)
        assert rx.received == []


def test_old_idempotency_records_are_cleaned_up(
    client: TestClient, admin: Headers, db: Session
) -> None:
    client.post("/v1/projects", headers={**admin, "Idempotency-Key": "k1"}, json={"name": "A"})
    dispatch.clean_up(db, now=utcnow() + timedelta(hours=23))
    assert db.scalars(select(IdempotencyRecord)).all() != []
    dispatch.clean_up(db, now=utcnow() + timedelta(hours=25))
    assert db.scalars(select(IdempotencyRecord)).all() == []


def test_ipv6_unreachable_reports_the_ipv4_cause_instead() -> None:
    unreachable = OSError(errno.ENETUNREACH, "Network is unreachable")
    # Nothing listens on port 9 (discard) locally, so IPv4 says the connection was refused.
    assert dispatch.describe_error("http://127.0.0.1:9/", unreachable) == "Connection refused"
    assert dispatch.describe_error("http://x/", ValueError("bad")) == "bad"
