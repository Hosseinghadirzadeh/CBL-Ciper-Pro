from __future__ import annotations

from argon2.low_level import Type, hash_secret_raw


DEFAULT_PARAMS = {"time_cost": 3, "memory_cost": 65536, "parallelism": 2, "hash_len": 32}


def derive_root_key(password: str, salt: bytes, params: dict | None = None) -> bytes:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must not be empty")
    p = {**DEFAULT_PARAMS, **(params or {})}
    return hash_secret_raw(password.encode("utf-8"), salt, p["time_cost"], p["memory_cost"], p["parallelism"], p["hash_len"], Type.ID)

