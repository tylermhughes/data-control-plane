"""Public IDs like prj_01jbx4k9r2... : a type prefix, a timestamp part, then randomness.

The timestamp part makes IDs sort by creation time, which cursor pagination relies on.
"""

import secrets
import time

_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"  # Crockford base32, lowercase


def new_id(prefix: str) -> str:
    ms = time.time_ns() // 1_000_000
    stamp = ""
    for _ in range(10):
        stamp = _ALPHABET[ms & 31] + stamp
        ms >>= 5
    rand = "".join(secrets.choice(_ALPHABET) for _ in range(16))
    return f"{prefix}_{stamp}{rand}"
