"""Send a signed delivery message to a DCP inbound webhook, like a vendor's system would.

    python3 scripts/send_inbound.py --url http://localhost:8000/v1/inbound/ihk_... \\
        --secret whsec_... --delivered 500 --spend 775 --external-ref surge-77

Built-in Python only (3.9+). Also a reference for senders: see sign().
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request
import uuid


def sign(secret: str, message_id: str, timestamp: int, body: bytes) -> str:
    key = base64.b64decode(secret.removeprefix("whsec_"))
    signed = f"{message_id}.{timestamp}.".encode() + body
    return "v1," + base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--url", required=True, help="The inbound webhook's full URL")
    parser.add_argument("--secret", required=True, help="The inbound webhook's whsec_... secret")
    parser.add_argument("--delivered", type=int, help="delivered_count")
    parser.add_argument("--spend", help="Spend, e.g. 775 (left out: DCP estimates it)")
    parser.add_argument("--external-ref", help="The source's id for this delivery")
    parser.add_argument("--file-uri", help="A file to check, e.g. s3://intake/surge/a.jsonl")
    parser.add_argument("--message-id", help="Defaults to a new random id")
    args = parser.parse_args()

    data: dict[str, object] = {}
    if args.delivered is not None:
        data["delivered_count"] = args.delivered
    if args.spend is not None:
        data["spend"] = args.spend
    if args.external_ref:
        data["external_ref"] = args.external_ref
    if args.file_uri:
        data["artifacts"] = [{"uri": args.file_uri, "format": args.file_uri.rsplit(".", 1)[-1]}]
    body = json.dumps({"type": "batch.delivered", "data": data}).encode()
    message_id = args.message_id or f"msg_{uuid.uuid4().hex}"
    timestamp = int(time.time())
    request = urllib.request.Request(  # noqa: S310 (the operator's own DCP)
        args.url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "webhook-id": message_id,
            "webhook-timestamp": str(timestamp),
            "webhook-signature": sign(args.secret, message_id, timestamp, body),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            print(f"HTTP {response.status}: {response.read().decode()}")
            return 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read().decode()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
