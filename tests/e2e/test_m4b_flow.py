"""M4b end to end: accepting a batch sends a signed webhook; a down receiver is retried."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import signing
from app.worker.__main__ import run_once
from tests.helpers import Headers, Setup, post_ok
from tests.receiver import running_receiver


def test_m4b_batch_accepted_webhook(client: TestClient, admin: Headers, db: Session) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    batch = s.batch(alloc["id"])

    with running_receiver() as rx:
        ep = post_ok(
            client,
            "/v1/webhook-endpoints",
            admin,
            {"project_id": s.project_id, "url": rx.url, "event_types": ["batch.accepted"]},
        )
        rx.status = 503  # receiver down at first
        client.post(
            f"/v1/batches/{batch['id']}/accept", headers=admin, json={"accepted_count": 900}
        )
        run_once(db)
        [failed] = client.get("/v1/webhook-deliveries", headers=admin).json()["data"]
        assert (failed["status"], failed["attempts"][0]["status_code"]) == ("pending", 503)

        rx.status = 200  # back up: re-send now instead of waiting for the retry
        client.post(f"/v1/webhook-deliveries/{failed['id']}/redeliver", headers=admin)
        run_once(db)

    msg = rx.received[-1]
    assert msg.json["type"] == "batch.accepted"
    assert msg.json["data"]["accepted_count"] == 900
    assert signing.verify(
        ep["secret"],
        msg.headers["webhook-id"],
        int(msg.headers["webhook-timestamp"]),
        msg.body,
        msg.headers["webhook-signature"],
    )
