from __future__ import annotations

import hashlib
import hmac


def hmac_sha256(key: bytes, *parts: bytes) -> bytes:
    return hmac.new(key, b"".join(parts), hashlib.sha256).digest()


def uint64(value: int) -> bytes:
    return value.to_bytes(8, "big", signed=False)

