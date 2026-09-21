from __future__ import annotations

import json
import struct

from app.constants import CBL_GEO_VERSION, FORMAT_VERSION, MAGIC
from core.errors import ContainerError
from core.token_codec import canonical_json


def pack(header: dict, ciphertext: bytes) -> bytes:
    header_bytes = canonical_json(header)
    return MAGIC + struct.pack(">BIQ", FORMAT_VERSION, len(header_bytes), len(ciphertext)) + header_bytes + ciphertext


def unpack(blob: bytes) -> tuple[dict, bytes, bytes]:
    prefix_size = 4 + struct.calcsize(">BIQ")
    if len(blob) < prefix_size or blob[:4] != MAGIC:
        raise ContainerError("Not a valid LBCX file")
    version, header_len, ciphertext_len = struct.unpack(">BIQ", blob[4:prefix_size])
    if version != FORMAT_VERSION:
        raise ContainerError(f"Unsupported LBCX format version: {version}")
    if header_len > 1024 * 1024 or ciphertext_len != len(blob) - prefix_size - header_len:
        raise ContainerError("Corrupted LBCX container lengths")
    raw_header = blob[prefix_size:prefix_size + header_len]
    try:
        header = json.loads(raw_header.decode("utf-8"))
    except Exception as exc:
        raise ContainerError("Corrupted LBCX header") from exc
    # Accept the pre-rename field so files from releases <= 1.0.1 remain readable.
    algorithm_version = header.get("cbl_geo_version", header.get("lbc_geo_version"))
    if algorithm_version != CBL_GEO_VERSION:
        raise ContainerError("Unsupported CBL-GEO version")
    aad = blob[:prefix_size] + raw_header
    return header, blob[prefix_size + header_len:], aad


def aad_for_header(header: dict, ciphertext_length: int) -> bytes:
    raw = canonical_json(header)
    return MAGIC + struct.pack(">BIQ", FORMAT_VERSION, len(raw), ciphertext_length) + raw
