from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from core.errors import AuthenticationError, CorpusError
from core.normalization import normalize_character, normalize_corpus
from core.random_engine import hmac_sha256, uint64
from core.token_codec import canonical_json, parse_json
from database.db import Database
from database.models import Book
from indexing.book_indexer import get_positions


@dataclass(frozen=True)
class EncodedUnit:
    book_ids: list[int]
    data: bytes


def _choose_books(key: bytes, nonce: bytes, index: int, candidates: list[Book], count: int) -> list[Book]:
    ranked = sorted(candidates, key=lambda b: hmac_sha256(key, nonce, uint64(index), uint64(b.external_id & ((1 << 64) - 1))))
    chosen, authors = [], set()
    for book in ranked:
        if book.author not in authors:
            chosen.append(book); authors.add(book.author)
        if len(chosen) == count:
            return chosen
    for book in ranked:
        if book not in chosen:
            chosen.append(book)
        if len(chosen) == count:
            return chosen
    return chosen


def encode_unit(db: Database, books: list[Book], unit: int | str, index: int, count: int, key: bytes, auth_key: bytes, nonce: bytes, *, binary: bool = False) -> EncodedUnit:
    character = "" if binary else normalize_character(str(unit))
    candidates = []
    if character and character == unit:
        candidates = [b for b in books if get_positions(db, b.id, character)]
    kind = "C" if len(candidates) >= count else "E"
    candidates = candidates if kind == "C" else books
    chosen = _choose_books(key, nonce, index, candidates, count)
    if len(chosen) < count:
        raise CorpusError(f"Not enough eligible books for {count} references")
    references = []
    for ref_index, book in enumerate(chosen):
        if kind == "C":
            positions = get_positions(db, book.id, character)
            random = hmac_sha256(key, nonce, uint64(index), uint64(ref_index))
            position = positions[int.from_bytes(random, "big") % len(positions)]
        else:
            position = -1
        references.append({"g": book.external_id, "p": position})
    payload = {"i": index, "r": references, "t": kind}
    if kind == "E":
        payload["b"] = int(unit) if binary else None
        if not binary:
            raise ValueError("Text escape units must be passed as UTF-8 bytes")
    serialized = canonical_json(payload)
    check = hmac.new(auth_key, serialized, hashlib.sha256).hexdigest()
    return EncodedUnit([r["g"] for r in references], canonical_json({"c": check, "p": payload}))


def decode_unit(db: Database, data: bytes, expected_index: int, auth_key: bytes) -> bytes:
    obj = parse_json(data)
    payload = obj["p"]
    serialized = canonical_json(payload)
    expected = hmac.new(auth_key, serialized, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, obj["c"]):
        raise AuthenticationError("Incorrect password or corrupted file.")
    if payload["i"] != expected_index:
        raise CorpusError("Invalid token sequence")
    if payload["t"] == "E":
        value = payload.get("b")
        if not isinstance(value, int) or not 0 <= value <= 255:
            raise CorpusError("Invalid escape token")
        return bytes([value])
    values = []
    for ref in payload["r"]:
        book = db.book_by_external_id(int(ref["g"]))
        if book is None:
            raise CorpusError(f"Required literary corpus book is missing: {ref['g']}")
        corpus = normalize_corpus(__import__("pathlib").Path(book.local_path).read_text(encoding="utf-8"))
        position = int(ref["p"])
        if position < 0 or position >= len(corpus):
            raise CorpusError("Literary reference is outside the indexed corpus")
        values.append(corpus[position])
    if not values or len(set(values)) != 1:
        raise CorpusError("Literary references disagree; corpus or token is invalid")
    return values[0].encode("utf-8")

