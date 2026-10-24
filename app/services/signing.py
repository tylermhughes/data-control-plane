"""Webhook signing, following the Standard Webhooks spec (https://www.standardwebhooks.com).

Each endpoint's secret is derived from DCP_SECRET_KEY, so no secret is ever stored:
    secret = HMAC-SHA256(master key, "webhook-secret:{endpoint id}:{version}")
Shown to users as "whsec_" + base64(secret). Each message is signed as
    base64(HMAC-SHA256(secret, "{message id}.{unix timestamp}.{body}"))
and sent in the `webhook-signature` header as "v1,<signature>" (space-separated when a
recently rotated endpoint is signed with both its new and previous secret).
"""

import base64
import hashlib
import hmac

from app.config import get_settings

PREFIX = "whsec_"


def endpoint_secret(endpoint_id: str, version: int) -> bytes:
    master = get_settings().dcp_secret_key.encode()
    return hmac.new(
        master, f"webhook-secret:{endpoint_id}:{version}".encode(), hashlib.sha256
    ).digest()


def display_secret(endpoint_id: str, version: int) -> str:
    return PREFIX + base64.b64encode(endpoint_secret(endpoint_id, version)).decode()


def sign(secret: bytes, message_id: str, timestamp: int, body: bytes) -> str:
    signed = f"{message_id}.{timestamp}.".encode() + body
    return "v1," + base64.b64encode(hmac.new(secret, signed, hashlib.sha256).digest()).decode()


def verify(secret_text: str, message_id: str, timestamp: int, body: bytes, header: str) -> bool:
    """What a receiver does. Used by tests and scripts/webhook_receiver.py's logic."""
    secret = base64.b64decode(secret_text.removeprefix(PREFIX))
    expected = sign(secret, message_id, timestamp, body)
    return any(hmac.compare_digest(expected, candidate) for candidate in header.split())
