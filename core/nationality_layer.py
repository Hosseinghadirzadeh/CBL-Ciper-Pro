from __future__ import annotations

import hashlib

from core.token_codec import canonical_json, xor_bytes
from crypto.hkdf_engine import derive_key, expand
from database.models import Book


def author_material(books: list[Book]) -> bytes:
    hashes = []
    for book in sorted(books, key=lambda b: b.external_id):
        descriptor = canonical_json([book.external_id, book.author.strip(), book.nationality.strip(), book.birth_country.strip(), book.birth_city.strip()])
        hashes.append(hashlib.sha3_512(descriptor).digest())
    return hashlib.sha3_512(b"".join(hashes)).digest()


def transform(data: bytes, books: list[Book], master_key: bytes, message_nonce: bytes, symbol_index: int) -> bytes:
    info = b"LBC-GEO nationality symbol" + message_nonce + symbol_index.to_bytes(8, "big")
    layer_key = derive_key(master_key, info, salt=author_material(books))
    mask = expand(layer_key, b"nationality-mask" + symbol_index.to_bytes(8, "big"), len(data))
    return xor_bytes(data, mask)

