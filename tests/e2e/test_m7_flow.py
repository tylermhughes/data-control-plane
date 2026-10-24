"""M7 end to end: a vendor pushes a delivery by signed webhook, and another arrives in a bucket."""

import importlib.util
import json
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.worker.__main__ import run_once
from tests import s3
from tests.helpers import Headers, Setup, post_ok

SENDER = Path(__file__).parents[2] / "scripts" / "send_inbound.py"


def test_m7_inbound_webhook_and_bucket_watcher(
    client: TestClient, admin: Headers, db: Session
) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation(quantity=4000, quoted_unit_rate="1.55")

    # 1. A vendor's system pushes a delivery, signed the way scripts/send_inbound.py signs.
    spec = importlib.util.spec_from_file_location("send_inbound", SENDER)
    assert spec and spec.loader
    sender = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sender)
    ep = post_ok(client, "/v1/inbound-webhooks", admin, {"data_source_id": s.sources["Surge"]})
    body = json.dumps(
        {"type": "batch.delivered", "data": {"delivered_count": 500, "external_ref": "surge-1"}}
    ).encode()
    ts = int(time.time())
    pushed = client.post(
        ep["url_path"],
        content=body,
        headers={
            "webhook-id": "msg_1",
            "webhook-timestamp": str(ts),
            "webhook-signature": sender.sign(ep["secret"], "msg_1", ts, body),
        },
    ).json()
    first = client.get(f"/v1/batches/{pushed['batch_id']}", headers=admin).json()
    assert first["spend"] == "775.00"  # no spend sent: estimated at 500 × 1.55
    assert first["spend_is_estimate"] is True

    # 2. Another delivery lands in the vendor's bucket; the watcher turns it into a batch.
    bucket = s3.new_bucket()
    post_ok(
        client,
        "/v1/connectors",
        admin,
        {
            "data_source_id": s.sources["Surge"],
            "bucket": bucket,
            "prefix": "surge/",
            "endpoint_url": s3.ENDPOINT,
            "credentials": {"access_key_id": s3.ACCESS_KEY, "secret_access_key": s3.SECRET_KEY},
        },
    )
    rows = [{"id": f"r{i}", "package_type": "box", "zone": "induct"} for i in range(120)]
    s3.put(bucket, "surge/drop-2.jsonl", "".join(json.dumps(r) + "\n" for r in rows).encode())
    run_once(db)  # polls the bucket and creates the batch
    run_once(db)  # runs its checks
    batches = client.get(f"/v1/batches?allocation_id={alloc['id']}", headers=admin).json()["data"]
    watched = next(b for b in batches if b["external_ref"] == "s3:surge/drop-2.jsonl")
    assert (watched["status"], watched["delivered_count"], watched["spend"]) == (
        "passed",
        120,
        "186.00",
    )
