from __future__ import annotations

import array
from collections import defaultdict
from pathlib import Path

from core.normalization import normalize_corpus
from database.db import Database


def encode_positions(values: list[int]) -> bytes:
    data = array.array("Q", values)
    if data.itemsize != 8:
        raise RuntimeError("Unsupported platform integer size")
    return data.tobytes()


def decode_positions(data: bytes) -> list[int]:
    values = array.array("Q")
    values.frombytes(data)
    return values.tolist()


def index_book(db: Database, book_id: int) -> int:
    book = next(b for b in db.books() if b.id == book_id)
    text = normalize_corpus(Path(book.local_path).read_text(encoding="utf-8", errors="strict"))
    positions: dict[str, list[int]] = defaultdict(list)
    for position, character in enumerate(text):
        positions[character].append(position)
    with db.session() as conn:
        conn.execute("DELETE FROM character_positions WHERE book_id=?", (book_id,))
        conn.executemany("INSERT INTO character_positions(book_id,character,positions) VALUES(?,?,?)", [(book_id, ch, encode_positions(pos)) for ch, pos in positions.items()])
        conn.execute("UPDATE books SET indexed=1,updated_at=CURRENT_TIMESTAMP WHERE id=?", (book_id,))
    return len(text)


def get_positions(db: Database, book_id: int, character: str) -> list[int]:
    with db.session() as conn:
        row = conn.execute("SELECT positions FROM character_positions WHERE book_id=? AND character=?", (book_id, character)).fetchone()
    return decode_positions(row[0]) if row else []
