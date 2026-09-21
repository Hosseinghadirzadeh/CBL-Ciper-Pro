from __future__ import annotations

import hashlib

import blake3
import pytest

from database.db import Database
from indexing.book_indexer import index_book


@pytest.fixture
def library(tmp_path):
    db = Database(tmp_path / "library.sqlite3")
    text = ("abcdefghijklmnopqrstuvwxyz0123456789" * 20) + "\nThe quick brown fox"
    metadata = [
        (1342, "Pride and Prejudice", "Jane Austen", "British", "England", "Steventon", 51.239, -1.105),
        (1661, "Sherlock Holmes", "Arthur Conan Doyle", "British", "Scotland", "Edinburgh", 55.9533, -3.1883),
        (2701, "Moby-Dick", "Herman Melville", "American", "United States", "New York", 40.7128, -74.006),
    ]
    for gid, title, author, nationality, country, city, lat, lon in metadata:
        path = tmp_path / f"{gid}.txt"
        raw = text.encode()
        path.write_bytes(raw)
        book_id = db.add_book(gutenberg_id=gid, title=title, author=author, local_path=str(path), sha256=hashlib.sha256(raw).hexdigest(), blake3=blake3.blake3(raw).hexdigest(), nationality=nationality, birth_country=country, birth_city=city, latitude=lat, longitude=lon)
        index_book(db, book_id)
    return db

