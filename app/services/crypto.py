"""Encryption for stored secrets (e.g. a connector's bucket keys).

Uses Fernet from the `cryptography` package (AES-128-CBC with an HMAC-SHA256 tag), with a
key derived from DCP_SECRET_KEY. Back up DCP_SECRET_KEY with the database: without it the
stored secrets can't be read.
"""

import base64
import hashlib
import hmac
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet:
    master = get_settings().dcp_secret_key.encode()
    key = hmac.new(master, b"dcp-encryption-key:v1", hashlib.sha256).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value: dict[str, Any]) -> str:
    return _fernet().encrypt(json.dumps(value).encode()).decode()


def decrypt(token: str) -> dict[str, Any]:
    try:
        data: dict[str, Any] = json.loads(_fernet().decrypt(token.encode()))
    except InvalidToken:
        raise ValueError(
            "Stored credentials can't be decrypted: DCP_SECRET_KEY has changed since they "
            "were saved. Save the credentials again."
        ) from None
    return data
