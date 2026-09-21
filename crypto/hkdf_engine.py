from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF, HKDFExpand


def derive_key(material: bytes, info: bytes, *, salt: bytes | None = None, length: int = 32) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(material)


def expand(key: bytes, info: bytes, length: int) -> bytes:
    return HKDFExpand(algorithm=hashes.SHA256(), length=length, info=info).derive(key)


def separate_keys(root_key: bytes) -> dict[str, bytes]:
    labels = {
        "literary": b"LBC-GEO literary layer",
        "nationality": b"LBC-GEO nationality layer",
        "geographic": b"LBC-GEO geographic layer",
        "aes": b"LBC-GEO AES-256-GCM",
        "token_auth": b"LBC-GEO token authentication",
    }
    return {name: derive_key(root_key, label) for name, label in labels.items()}

