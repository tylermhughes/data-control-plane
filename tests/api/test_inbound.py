"""Inbound webhooks: signed messages from a source's systems become batches."""

import base64
import json
import time
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InboundMessage
from app.services import signing
from tests.conftest import MakeKey
from tests.helpers import Headers, Setup, post_ok


def send(
    client: TestClient,
    ep: Any,
    message: Any,
    *,
    secret: str | None = None,
    message_id: str = "msg_1",
    timestamp: int | None = None,
) -> Any:
    body = json.dumps(message).encode()
    ts = timestamp if timestamp is not None else int(time.time())
    key = secret or ep["secret"]
    signature = signing.sign(base64.b64decode(key.removeprefix("whsec_")), message_id, ts, body)
    return client.post(
        ep["url_path"],
        content=body,
        headers={
            "webhook-id": message_id,
            "webhook-timestamp": str(ts),
            "webhook-signature": signature,
            "Content-Type": "application/json",
        },
    )


def delivery(**data: Any) -> dict[str, Any]:
    return {"type": "batch.delivered", "data": {"delivered_count": 500, "spend": "775", **data}}


def endpoint(s: Setup, source: str = "Surge") -> Any:
    return post_ok(s.client, "/v1/inbound-webhooks", s.admin, {"data_source_id": s.sources[source]})


def test_signed_message_creates_a_batch(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    ep = endpoint(s)
    assert ep["id"].startswith("ihk_")
    assert ep["url_path"] == f"/v1/inbound/{ep['id']}"
    assert ep["secret"].startswith("whsec_")

    response = send(client, ep, delivery(external_ref="surge-77"))  # no API key needed
    assert response.status_code == 200, response.text
    result = response.json()
    assert (result["status"], result["duplicate"], result["batch_status"]) == (
        "processed",
        False,
        "received",
    )
    batch = client.get(f"/v1/batches/{result['batch_id']}", headers=admin).json()
    assert batch["allocation_id"] == alloc["id"]  # the source's only active allocation
    assert (batch["delivered_count"], batch["external_ref"]) == (500, "surge-77")

    log = client.get(f"/v1/inbound-webhooks/{ep['id']}/messages", headers=admin).json()["data"]
    assert [(m["status"], m["message_id"], m["batch_id"]) for m in log] == [
        ("processed", "msg_1", result["batch_id"])
    ]
    assert client.get(f"/v1/inbound-webhooks/{ep['id']}", headers=admin).json()["last_received_at"]


def test_same_message_twice_returns_the_first_result(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    s.active_allocation()
    ep = endpoint(s)
    first = send(client, ep, delivery()).json()
    again = send(client, ep, delivery()).json()
    assert (again["batch_id"], again["duplicate"]) == (first["batch_id"], True)
    batches = client.get("/v1/batches", headers=admin).json()["data"]
    assert len(batches) == 1


def test_bad_messages_are_refused_and_logged(
    client: TestClient, admin: Headers, db: Session
) -> None:
    s = Setup(client, admin)
    s.active_allocation()
    ep = endpoint(s)
    other = endpoint(s)

    cases = {
        "wrong secret": (send(client, ep, delivery(), secret=other["secret"], message_id="a"), 401),
        "too old": (
            send(client, ep, delivery(), message_id="b", timestamp=int(time.time()) - 600),
            401,
        ),
        "unknown type": (send(client, ep, {"type": "x.y", "data": {}}, message_id="c"), 422),
        "bad data": (send(client, ep, delivery(spend="-5"), message_id="d"), 422),
        "no count, no files": (
            send(client, ep, {"type": "batch.delivered", "data": {"spend": "1"}}, message_id="e"),
            422,
        ),
    }
    for label, (response, expected) in cases.items():
        assert response.status_code == expected, (label, response.text)
        assert response.headers["content-type"] == "application/problem+json"

    unsigned = client.post(ep["url_path"], json=delivery())
    assert unsigned.status_code == 401
    assert "Missing webhook-id" in unsigned.json()["detail"]

    logged = db.scalars(select(InboundMessage).where(InboundMessage.endpoint_id == ep["id"])).all()
    assert len(logged) == 6
    assert all(m.status == "rejected" for m in logged)
    assert {m.message_id for m in logged} >= {"a", "b", "c", "d", "e"}
    assert client.get("/v1/batches", headers=admin).json()["data"] == []


def test_allocation_must_be_clear(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    ep = endpoint(s)
    none = send(client, ep, delivery(), message_id="1")
    assert none.status_code == 409
    assert "no active allocation" in none.json()["detail"]

    first = s.active_allocation()
    second = s.active_allocation()
    ambiguous = send(client, ep, delivery(), message_id="2")
    assert ambiguous.status_code == 409
    assert "2 active allocations" in ambiguous.json()["detail"]
    named = send(client, ep, delivery(allocation_id=second["id"]), message_id="3")
    assert named.status_code == 200

    mercor = s.active_allocation("Mercor")
    wrong_source = send(client, ep, delivery(allocation_id=mercor["id"]), message_id="4")
    assert wrong_source.status_code == 422
    assert first["id"]


def test_disabled_endpoint_refuses(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    s.active_allocation()
    ep = endpoint(s)
    client.patch(f"/v1/inbound-webhooks/{ep['id']}", headers=admin, json={"enabled": False})
    assert send(client, ep, delivery()).status_code == 403
    assert client.post("/v1/inbound/ihk_nope", json={}).status_code == 404


def test_rotation_keeps_the_old_secret_for_a_day(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    s.active_allocation()
    ep = endpoint(s)
    rotated = client.post(f"/v1/inbound-webhooks/{ep['id']}/rotate-secret", headers=admin).json()
    assert rotated["secret"] != ep["secret"]
    assert rotated["previous_secret_valid_until"]
    assert send(client, ep, delivery(), message_id="old").status_code == 200
    assert (
        send(client, ep, delivery(), secret=rotated["secret"], message_id="new").status_code == 200
    )


def test_messages_can_import_decisions_and_update_by_external_ref(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    s.active_allocation()
    ep = endpoint(s)
    decided = delivery(
        external_ref="lb-9",
        decision={"status": "accepted", "decided_by": "labelbox", "accepted_count": 450},
    )
    first = send(client, ep, decided, message_id="m1").json()
    decided["data"]["decision"]["accepted_count"] = 470
    second = send(client, ep, decided, message_id="m2").json()
    assert second["batch_id"] == first["batch_id"]
    batch = client.get(f"/v1/batches/{first['batch_id']}", headers=admin).json()
    assert (batch["status"], batch["accepted_count"]) == ("accepted", 470)


def test_project_keys_manage_only_their_project(
    client: TestClient, admin: Headers, make_key: MakeKey
) -> None:
    mine, theirs = Setup(client, admin, "Mine"), Setup(client, admin, "Theirs")
    key = make_key(role="project", project_id=mine.project_id)
    other = endpoint(theirs)
    assert client.get(f"/v1/inbound-webhooks/{other['id']}", headers=key).status_code == 404
    sneaky = client.post(
        "/v1/inbound-webhooks", headers=key, json={"data_source_id": theirs.sources["Surge"]}
    )
    assert sneaky.status_code == 422
    own = client.post(
        "/v1/inbound-webhooks", headers=key, json={"data_source_id": mine.sources["Surge"]}
    )
    assert own.status_code == 201


def test_data_source_with_intake_cannot_be_deleted(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    ep = endpoint(s, "Mercor")
    response = client.delete(f"/v1/data-sources/{s.sources['Mercor']}", headers=admin)
    assert response.status_code == 409
    assert "inbound webhooks" in response.json()["detail"]
    client.delete(f"/v1/inbound-webhooks/{ep['id']}", headers=admin)
    assert (
        client.delete(f"/v1/data-sources/{s.sources['Mercor']}", headers=admin).status_code == 204
    )
