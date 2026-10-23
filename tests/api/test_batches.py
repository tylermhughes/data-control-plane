from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from tests.helpers import Headers, Setup

COUNTS = {"package_type": {"box": 400, "shrink_wrapped": 350}, "zone": {"induct": 600}}


def test_register_a_delivery(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    batch = s.batch(
        alloc["id"],
        delivered_count=1000,
        spend="1550.00",
        contributor_count=12,
        artifacts=[{"uri": "s3://intake/surge/b1.jsonl", "format": "jsonl", "record_count": 1000}],
    )
    assert batch["id"].startswith("bat_")
    assert batch["status"] == "received"
    assert batch["currency"] == "USD"  # the allocation's
    assert batch["spec_version_id"] == s.v1
    assert batch["request_id"] == alloc["request_id"]
    assert batch["data_source_id"] == alloc["data_source_id"]
    assert (batch["accepted_count"], batch["rejected_count"]) == (None, None)
    assert batch["artifacts"][0]["uri"] == "s3://intake/surge/b1.jsonl"


def test_accept_part_of_a_delivery(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"])
    accepted = client.post(
        f"/v1/batches/{batch['id']}/accept",
        headers=admin,
        json={"accepted_count": 940, "attribute_counts": COUNTS, "decided_by": "Dana Okafor"},
    ).json()
    assert accepted["status"] == "accepted"
    assert (accepted["accepted_count"], accepted["rejected_count"]) == (940, 60)
    assert accepted["attribute_counts"] == COUNTS
    assert accepted["decision_source"] == "dcp"
    assert accepted["decided_by"] == "Dana Okafor"
    assert accepted["decided_by_key_id"].startswith("key_")


def test_reject_needs_a_reason(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"])
    path = f"/v1/batches/{batch['id']}/reject"
    assert client.post(path, headers=admin, json={}).status_code == 422
    rejected = client.post(path, headers=admin, json={"reason": "Agreement 0.81 < 0.85"}).json()
    assert (rejected["status"], rejected["accepted_count"]) == ("rejected", 0)
    assert rejected["rejection_reason"] == "Agreement 0.81 < 0.85"


def test_counts_are_checked(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"], delivered_count=1000)
    path = f"/v1/batches/{batch['id']}/accept"
    cases = {
        "more accepted than delivered": {"accepted_count": 1001},
        "unknown attribute": {"accepted_count": 10, "attribute_counts": {"colour": {"red": 1}}},
        "unknown value": {"accepted_count": 10, "attribute_counts": {"zone": {"dock": 1}}},
        "more than accepted": {"accepted_count": 10, "attribute_counts": {"zone": {"sort": 11}}},
    }
    for label, body in cases.items():
        response = client.post(path, headers=admin, json=body)
        assert response.status_code == 422, label
    assert client.get(f"/v1/batches/{batch['id']}", headers=admin).json()["status"] == "received"


def test_decisions_are_final_except_notes(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"])
    client.post(f"/v1/batches/{batch['id']}/accept", headers=admin, json={"accepted_count": 900})
    path = f"/v1/batches/{batch['id']}"

    assert client.patch(path, headers=admin, json={"notes": "Invoice 4471"}).status_code == 200
    frozen = client.patch(path, headers=admin, json={"spend": "1"})
    assert frozen.status_code == 409
    assert "only notes can change" in frozen.json()["detail"]
    assert client.post(f"{path}/reject", headers=admin, json={"reason": "x"}).status_code == 409
    assert (
        client.post(f"{path}/accept", headers=admin, json={"accepted_count": 1}).status_code == 409
    )
    assert client.delete(path, headers=admin).status_code == 409


def test_undecided_batches_can_change_and_be_deleted(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    batch = s.batch(s.active_allocation()["id"])
    path = f"/v1/batches/{batch['id']}"
    edited = client.patch(path, headers=admin, json={"delivered_count": 1040, "spend": "1612"})
    assert (edited.json()["delivered_count"], edited.json()["spend"]) == (1040, "1612.00")
    assert client.delete(path, headers=admin).status_code == 204


def test_allocation_must_be_active_and_currency_must_match(
    client: TestClient, admin: Headers
) -> None:
    s = Setup(client, admin)
    planned = s.allocate(s.open_request()["id"], "Surge")
    body = {"allocation_id": planned["id"], "delivered_count": 1, "spend": "1"}
    response = client.post("/v1/batches", headers=admin, json=body)
    assert response.status_code == 409
    assert "active allocations" in response.json()["detail"]

    active = s.active_allocation()
    wrong = client.post(
        "/v1/batches",
        headers=admin,
        json={"allocation_id": active["id"], "delivered_count": 1, "spend": "1", "currency": "EUR"},
    )
    assert wrong.status_code == 422
    assert "allocation's currency (USD)" in wrong.json()["detail"]


def test_totals_roll_up(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation(quantity=4000, quoted_unit_rate="1.55")
    a = s.batch(alloc["id"], delivered_count=2000, spend="3100")
    b = s.batch(alloc["id"], delivered_count=1000, spend="1550")
    s.batch(alloc["id"], delivered_count=500, spend="775")  # still undecided
    client.post(f"/v1/batches/{a['id']}/accept", headers=admin, json={"accepted_count": 1900})
    client.post(f"/v1/batches/{b['id']}/reject", headers=admin, json={"reason": "Off spec"})

    got = client.get(f"/v1/allocations/{alloc['id']}", headers=admin).json()
    assert got["batch_count"] == 3
    assert got["delivered_count"] == 3500
    assert got["accepted_count"] == 1900  # only accepted batches count
    assert got["spend"] == "5425.00"  # every delivery's spend counts
    assert got["progress"] == 0.475  # 1900 / 4000

    totals = client.get(f"/v1/requests/{alloc['request_id']}", headers=admin).json()["allocated"]
    assert totals == [
        {
            "unit": "images",
            "currency": "USD",
            "quantity": 4000,
            "quoted_cost": "6200.00",
            "delivered_count": 3500,
            "accepted_count": 1900,
            "spend": "5425.00",
        }
    ]


def test_events_for_each_step(client: TestClient, admin: Headers, db: Session) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    kept = s.batch(alloc["id"])
    dropped = s.batch(alloc["id"])
    client.post(f"/v1/batches/{kept['id']}/accept", headers=admin, json={"accepted_count": 1})
    client.post(f"/v1/batches/{dropped['id']}/reject", headers=admin, json={"reason": "x"})
    types = db.scalars(
        select(Event.type).where(Event.type.like("batch.%")).order_by(Event.id)
    ).all()
    assert types == ["batch.received", "batch.received", "batch.accepted", "batch.rejected"]


def test_list_filters(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    first = s.active_allocation("Surge")
    second = s.active_allocation("Mercor")
    kept = s.batch(first["id"])
    s.batch(second["id"])
    client.post(f"/v1/batches/{kept['id']}/accept", headers=admin, json={"accepted_count": 1})

    def ids(query: str) -> list[str]:
        return [b["id"] for b in client.get(f"/v1/batches?{query}", headers=admin).json()["data"]]

    assert ids(f"allocation_id={first['id']}") == [kept["id"]]
    assert ids(f"request_id={first['request_id']}") == [kept["id"]]
    assert ids(f"data_source_id={s.sources['Surge']}") == [kept["id"]]
    assert ids("status=accepted") == [kept["id"]]
    assert len(ids("status=received")) == 1
