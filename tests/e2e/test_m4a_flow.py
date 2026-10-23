"""M4a end to end: the steps Tyler follows in /docs, through the real API and database."""

from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup


def test_m4a_deliveries_decided_here_and_elsewhere(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation(quantity=12000, quoted_unit_rate="1.55")

    # 1. A delivery arrives and is accepted in DCP: 11,290 of 12,000 kept.
    first = s.batch(alloc["id"], delivered_count=12000, spend="18600", contributor_count=46)
    client.post(
        f"/v1/batches/{first['id']}/accept",
        headers=admin,
        json={"accepted_count": 11290, "attribute_counts": {"package_type": {"box": 4100}}},
    )

    # 2. A second delivery is imported already rejected by the vendor's QA.
    second = s.batch(
        alloc["id"],
        delivered_count=500,
        spend="0",
        external_ref="surge-2043",
        decision={"status": "rejected", "decided_by": "surge", "reason": "Failed gold set"},
    )
    assert second["decision_source"] == "external"

    # 3. The allocation's totals and progress update.
    got = client.get(f"/v1/allocations/{alloc['id']}", headers=admin).json()
    assert (got["delivered_count"], got["accepted_count"], got["spend"]) == (
        12500,
        11290,
        "18600.00",
    )
    assert got["progress"] == round(11290 / 12000, 4)
