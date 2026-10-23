"""Batches decided outside DCP (vendor QA, Labelbox, ...) and re-imported over time."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from tests.helpers import Headers, Setup


def imported(alloc_id: str, **extra: Any) -> dict[str, Any]:
    return {
        "allocation_id": alloc_id,
        "delivered_count": 12000,
        "spend": "18600",
        "external_ref": "labelbox-export-118",
        "external_url": "https://app.labelbox.com/exports/118",
        "decision": {
            "status": "accepted",
            "decided_by": "labelbox",
            "accepted_count": 11290,
            "attribute_counts": {"package_type": {"box": 4100, "shrink_wrapped": 3300}},
        },
        **extra,
    }


def test_import_an_accepted_batch_in_one_call(
    client: TestClient, admin: Headers, db: Session
) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    response = client.post("/v1/batches", headers=admin, json=imported(alloc["id"]))
    assert response.status_code == 201
    batch = response.json()
    assert batch["status"] == "accepted"
    assert batch["decision_source"] == "external"
    assert batch["decided_by"] == "labelbox"
    assert batch["decided_by_key_id"] is None
    assert (batch["accepted_count"], batch["rejected_count"]) == (11290, 710)
    assert batch["external_ref"] == "labelbox-export-118"

    types = db.scalars(select(Event.type).where(Event.subject_id == batch["id"]).order_by(Event.id))
    assert list(types) == ["batch.received", "batch.accepted"]


def test_import_a_rejected_batch(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    body = imported(
        alloc["id"],
        decision={"status": "rejected", "decided_by": "surge", "reason": "Failed gold set"},
    )
    batch = client.post("/v1/batches", headers=admin, json=body).json()
    assert (batch["status"], batch["accepted_count"]) == ("rejected", 0)
    assert batch["rejection_reason"] == "Failed gold set"


def test_external_decision_is_validated(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc_id = s.active_allocation()["id"]
    bad = [
        {"status": "accepted", "decided_by": "labelbox"},  # no accepted_count
        {"status": "rejected", "decided_by": "surge"},  # no reason
        {"status": "accepted", "accepted_count": 5},  # no decided_by
        {"status": "accepted", "decided_by": "x", "accepted_count": 99999},  # > delivered
    ]
    for decision in bad:
        body = imported(alloc_id, decision=decision, external_ref=None)
        assert client.post("/v1/batches", headers=admin, json=body).status_code == 422, decision


def test_identical_reimport_changes_nothing(
    client: TestClient, admin: Headers, db: Session
) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    first = client.post("/v1/batches", headers=admin, json=imported(alloc["id"])).json()
    again = client.post("/v1/batches", headers=admin, json=imported(alloc["id"]))
    assert again.status_code == 200
    assert again.json() == first
    events = db.scalars(select(Event.type).where(Event.subject_id == first["id"])).all()
    assert "batch.reimported" not in events


def test_reimport_with_new_numbers_updates_and_records_changes(
    client: TestClient, admin: Headers, db: Session
) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    first = client.post("/v1/batches", headers=admin, json=imported(alloc["id"])).json()

    revised = imported(alloc["id"])
    revised["decision"]["accepted_count"] = 11350
    response = client.post("/v1/batches", headers=admin, json=revised)
    assert response.status_code == 200
    assert response.json()["id"] == first["id"]
    assert response.json()["accepted_count"] == 11350

    event = db.scalars(
        select(Event).where(Event.subject_id == first["id"], Event.type == "batch.reimported")
    ).one()
    assert event.data["changes"]["accepted_count"] == [11290, 11350]
    assert event.data["changes"]["rejected_count"] == [710, 650]
    assert set(event.data["changes"]) == {"accepted_count", "rejected_count"}


def test_reimport_can_add_a_decision_later(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    undecided = imported(alloc["id"])
    del undecided["decision"]
    first = client.post("/v1/batches", headers=admin, json=undecided).json()
    assert first["status"] == "received"

    later = client.post("/v1/batches", headers=admin, json=imported(alloc["id"])).json()
    assert (later["id"], later["status"]) == (first["id"], "accepted")


def test_reimport_without_decision_keeps_the_earlier_one(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    client.post("/v1/batches", headers=admin, json=imported(alloc["id"]))
    no_decision = imported(alloc["id"], notes="Re-synced")
    del no_decision["decision"]
    again = client.post("/v1/batches", headers=admin, json=no_decision).json()
    assert (again["status"], again["accepted_count"], again["notes"]) == (
        "accepted",
        11290,
        "Re-synced",
    )


def test_batches_decided_in_dcp_cannot_be_overwritten_by_import(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    undecided = imported(alloc["id"])
    del undecided["decision"]
    batch = client.post("/v1/batches", headers=admin, json=undecided).json()
    client.post(f"/v1/batches/{batch['id']}/accept", headers=admin, json={"accepted_count": 5})

    response = client.post("/v1/batches", headers=admin, json=imported(alloc["id"]))
    assert response.status_code == 409
    assert "accepted in DCP" in response.json()["detail"]


def test_external_ref_is_unique_per_source_not_globally(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    surge = s.active_allocation("Surge")
    mercor = s.active_allocation("Mercor")
    a = client.post("/v1/batches", headers=admin, json=imported(surge["id"])).json()
    b = client.post("/v1/batches", headers=admin, json=imported(mercor["id"])).json()
    assert a["id"] != b["id"]  # same external_ref, different sources

    other_alloc_same_source = s.active_allocation("Surge")
    clash = client.post("/v1/batches", headers=admin, json=imported(other_alloc_same_source["id"]))
    assert clash.status_code == 409
    assert "already belongs to batch" in clash.json()["detail"]


def test_reimport_works_after_allocation_completes(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    client.post("/v1/batches", headers=admin, json=imported(alloc["id"]))
    s.act("allocations", alloc["id"], "complete")

    revised = imported(alloc["id"], spend="18400")
    response = client.post("/v1/batches", headers=admin, json=revised)
    assert response.status_code == 200
    assert response.json()["spend"] == "18400.00"

    brand_new = imported(alloc["id"], external_ref="labelbox-export-119")
    assert client.post("/v1/batches", headers=admin, json=brand_new).status_code == 409
