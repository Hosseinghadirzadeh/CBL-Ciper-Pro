from __future__ import annotations

import hashlib

from core.token_codec import xor_bytes
from crypto.hkdf_engine import derive_key, expand
from database.models import Book
from geography.country_codes import country_code


def geographic_material(books: list[Book]) -> bytes:
    hashes = []
    for book in sorted(books, key=lambda b: b.external_id):
        descriptor = f"{country_code(book.birth_country)}|{book.birth_city.strip()}|{book.latitude:.6f}|{book.longitude:.6f}".encode("utf-8")
        hashes.append(hashlib.sha3_256(descriptor).digest())
    return hashlib.sha3_512(b"".join(hashes)).digest()


def transform(data: bytes, books: list[Book], master_key: bytes, message_nonce: bytes, symbol_index: int) -> bytes:
    info = b"LBC-GEO geographic symbol" + message_nonce + symbol_index.to_bytes(8, "big")
    layer_key = derive_key(master_key, info, salt=geographic_material(books))
    mask = expand(layer_key, b"geo-mask" + symbol_index.to_bytes(8, "big"), len(data))
    return xor_bytes(data, mask)

