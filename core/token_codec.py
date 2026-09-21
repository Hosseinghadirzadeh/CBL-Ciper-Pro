from __future__ import annotations

import base64
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def parse_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"), validate=True)


def xor_bytes(left: bytes, right: bytes) -> bytes:
    if len(left) != len(right):
        raise ValueError("XOR operands must be the same length")
    return bytes(a ^ b for a, b in zip(left, right))

