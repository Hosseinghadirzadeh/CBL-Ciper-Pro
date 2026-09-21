from __future__ import annotations

import hashlib
from typing import Callable

from core.geographic_layer import transform as geographic_transform
from core.literary_layer import decode_unit, encode_unit
from core.nationality_layer import transform as nationality_transform
from core.token_codec import b64d, b64e, canonical_json, parse_json
from core.validation import require_ready_books, verify_book
from database.db import Database
from database.models import Book


def book_descriptor(book: Book) -> bytes:
    return canonical_json([book.external_id, book.title, book.author, book.nationality, book.birth_country, book.birth_city, None if book.latitude is None else f"{book.latitude:.6f}", None if book.longitude is None else f"{book.longitude:.6f}", book.sha256, book.normalization_version])


def library_fingerprint(books: list[Book]) -> str:
    fingerprints = [hashlib.sha3_512(book_descriptor(book)).digest() for book in sorted(books, key=lambda b: b.external_id)]
    return hashlib.sha3_512(b"".join(fingerprints)).hexdigest()


def manifest_for(books: list[Book]) -> list[dict]:
    return [{"gutenberg_id": b.external_id, "sha256": b.sha256, "normalization_version": b.normalization_version, "title": b.title} for b in sorted(books, key=lambda x: x.external_id)]


class LBCGeoCipher:
    def __init__(self, db: Database):
        self.db = db

    def encode(self, data: bytes, keys: dict[str, bytes], message_nonce: bytes, books_per_symbol: int = 3, *, text: bool = False, progress: Callable[[int], None] | None = None) -> dict:
        books = sorted(self.db.books(ready_only=True), key=lambda b: b.external_id)
        require_ready_books(books, books_per_symbol)
        for book in books:
            verify_book(book)
        tokens, index = [], 0
        # Text is intentionally converted unit-by-unit: corpus-safe lowercase
        # alphanumerics use references; every other Unicode scalar uses ESCAPE_UTF8.
        units: list[tuple[int | str, bool]] = []
        if text:
            decoded = data.decode("utf-8")
            from core.normalization import normalize_character
            from indexing.book_indexer import get_positions
            for char in decoded:
                normalized = normalize_character(char)
                available = sum(bool(get_positions(self.db, book.id, normalized)) for book in books) if normalized else 0
                if normalized == char and available >= books_per_symbol:
                    units.append((char, False))
                else:
                    units.extend((byte, True) for byte in char.encode("utf-8"))
        else:
            units = [(byte, True) for byte in data]
        for unit, binary in units:
            encoded = encode_unit(self.db, books, unit, index, books_per_symbol, keys["literary"], keys["token_auth"], message_nonce, binary=binary)
            selected = [self.db.book_by_external_id(gid) for gid in encoded.book_ids]
            if any(book is None for book in selected):
                raise RuntimeError("Selected book disappeared")
            layer2 = nationality_transform(encoded.data, selected, keys["nationality"], message_nonce, index)
            layer3 = geographic_transform(layer2, selected, keys["geographic"], message_nonce, index)
            tokens.append({"g": encoded.book_ids, "x": b64e(layer3)})
            index += 1
            if progress and index % 100 == 0:
                progress(int(index * 100 / max(1, len(units))))
        return {"kind": "text" if text else "binary", "tokens": tokens, "manifest": manifest_for(books), "library_fingerprint": library_fingerprint(books)}

    def decode(self, payload: dict, keys: dict[str, bytes], message_nonce: bytes, progress: Callable[[int], None] | None = None) -> bytes:
        manifest = payload.get("manifest", [])
        for item in manifest:
            book = self.db.book_by_external_id(int(item["gutenberg_id"]))
            if book is None:
                from core.errors import CorpusError
                raise CorpusError(f"Required literary corpus book is missing: {item['title']}")
            if book.sha256 != item["sha256"] or book.normalization_version != item["normalization_version"]:
                from core.errors import CorpusError
                raise CorpusError("Required literary corpus does not match the encrypted data.")
            verify_book(book)
        output = bytearray()
        tokens = payload.get("tokens", [])
        for index, token in enumerate(tokens):
            books = [self.db.book_by_external_id(int(gid)) for gid in token["g"]]
            if any(book is None for book in books):
                from core.errors import CorpusError
                raise CorpusError("Required literary corpus book is missing")
            layer2 = geographic_transform(b64d(token["x"]), books, keys["geographic"], message_nonce, index)
            layer1 = nationality_transform(layer2, books, keys["nationality"], message_nonce, index)
            output.extend(decode_unit(self.db, layer1, index, keys["token_auth"]))
            if progress and index % 100 == 0:
                progress(int((index + 1) * 100 / max(1, len(tokens))))
        result = bytes(output)
        if payload.get("kind") == "text":
            try:
                result.decode("utf-8")
            except UnicodeDecodeError as exc:
                from core.errors import CorpusError
                raise CorpusError("Decoded text is not valid UTF-8") from exc
        return result
