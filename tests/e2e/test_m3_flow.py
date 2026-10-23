"""M3 end to end: the steps Tyler follows in /docs, through the real API and database."""

from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup


def test_m3_request_split_across_three_sources(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)

    # 1. A request for the capability, with the approved spec, opened.
    req = s.request(title="Shrink-wrapped packaging", quantity=10000, priority="P1")
    assert s.act("requests", req["id"], "open").json()["status"] == "open"

    # 2. Split across two vendors and one internal source.
    s.allocate(req["id"], "Surge", quantity=4000, quoted_unit_rate="1.55")
    s.allocate(req["id"], "Mercor", quantity=4000, quoted_unit_rate="1.65")
    s.allocate(req["id"], "Returns photos", quantity=3000, quoted_unit_rate="0.20")

    # 3. Total quoted cost: 6200 + 6600 + 600.
    totals = client.get(f"/v1/requests/{req['id']}", headers=admin).json()["allocated"]
    assert totals == [
        {"unit": "images", "currency": "USD", "quantity": 11000, "quoted_cost": "13400.00"}
    ]

    # 4. The spec is in use, so it can't be deleted.
    assert client.delete(f"/v1/specs/{s.spec_id}", headers=admin).status_code == 409
