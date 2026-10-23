"""Public IDs like prj_01jbx4k9r2... : a type prefix, a timestamp part, then randomness.

IDs sort by creation time, which cursor pagination and event ordering rely on. Within one
process they are strictly increasing, even for IDs made in the same millisecond.
"""

import secrets
import threading
import time

_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"  # Crockford base32, lowercase
_RANDOM_BITS = 80  # 16 base32 characters
_lock = threading.Lock()
_last_ms = -1
_last_random = 0


def _encode(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        chars.append(_ALPHABET[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def new_id(prefix: str) -> str:
    global _last_ms, _last_random
    with _lock:
        ms = time.time_ns() // 1_000_000
        if ms <= _last_ms:
            # Same millisecond (or the clock stepped back): count up from the last ID.
            ms, rand = _last_ms, _last_random + 1
            if rand >= 1 << _RANDOM_BITS:
                ms, rand = ms + 1, secrets.randbits(_RANDOM_BITS - 1)
        else:
            rand = secrets.randbits(_RANDOM_BITS - 1)  # leave room to count up
        _last_ms, _last_random = ms, rand
    return f"{prefix}_{_encode(ms, 10)}{_encode(rand, 16)}"
