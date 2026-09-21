from __future__ import annotations

import hashlib
from pathlib import Path

import blake3


ALGORITHMS = {"SHA-256": "sha256", "SHA-512": "sha512", "SHA3-256": "sha3_256", "SHA3-512": "sha3_512"}


def hash_bytes(data: bytes, algorithm: str = "SHA-256") -> str:
    if algorithm == "BLAKE3":
        return blake3.blake3(data).hexdigest()
    return hashlib.new(ALGORITHMS[algorithm], data).hexdigest()


def hash_file(path: str | Path, algorithm: str = "SHA-256", chunk_size: int = 1024 * 1024) -> str:
    digest = blake3.blake3() if algorithm == "BLAKE3" else hashlib.new(ALGORITHMS[algorithm])
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

