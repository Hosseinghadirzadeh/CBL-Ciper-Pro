from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from database.models import Book


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self.session() as conn:
            conn.executescript(schema)

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def session(self):
        conn = self.connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def add_book(self, *, gutenberg_id: int | None, title: str, author: str, local_path: str, sha256: str, blake3: str, language: str = "UNKNOWN", nationality: str = "UNKNOWN", birth_country: str = "UNKNOWN", birth_city: str = "UNKNOWN", latitude: float | None = None, longitude: float | None = None, metadata_source: str = "user") -> int:
        with self.session() as conn:
            conn.execute("INSERT INTO authors(full_name,nationality,birth_country,birth_city,latitude,longitude,metadata_source) VALUES(?,?,?,?,?,?,?) ON CONFLICT(full_name) DO UPDATE SET nationality=excluded.nationality,birth_country=excluded.birth_country,birth_city=excluded.birth_city,latitude=excluded.latitude,longitude=excluded.longitude,metadata_source=excluded.metadata_source", (author, nationality, birth_country, birth_city, latitude, longitude, metadata_source))
            author_id = conn.execute("SELECT id FROM authors WHERE full_name=?", (author,)).fetchone()[0]
            cur = conn.execute("INSERT INTO books(gutenberg_id,title,author_id,language,local_path,sha256,blake3,normalization_version) VALUES(?,?,?,?,?,?,?,1)", (gutenberg_id, title, author_id, language, str(local_path), sha256, blake3))
            return int(cur.lastrowid)

    def books(self, *, ready_only: bool = False) -> list[Book]:
        query = "SELECT b.*,a.full_name author,a.nationality,a.birth_country,a.birth_city,a.latitude,a.longitude FROM books b JOIN authors a ON a.id=b.author_id"
        with self.session() as conn:
            rows = conn.execute(query).fetchall()
        books = [Book(id=r["id"], gutenberg_id=r["gutenberg_id"], title=r["title"], author=r["author"], nationality=r["nationality"], birth_country=r["birth_country"], birth_city=r["birth_city"], latitude=r["latitude"], longitude=r["longitude"], local_path=r["local_path"], sha256=r["sha256"], blake3=r["blake3"], normalization_version=r["normalization_version"], indexed=bool(r["indexed"]), language=r["language"]) for r in rows]
        return [b for b in books if b.metadata_ready and b.indexed] if ready_only else books

    def book_by_external_id(self, external_id: int) -> Book | None:
        return next((b for b in self.books() if b.external_id == external_id), None)

    def update_book_metadata(self, external_id: int, *, author: str, nationality: str, birth_country: str, birth_city: str, latitude: float, longitude: float, metadata_source: str) -> None:
        book = self.book_by_external_id(external_id)
        if book is None:
            raise ValueError(f"Book {external_id} is not in the library")
        with self.session() as conn:
            conn.execute(
                "UPDATE authors SET full_name=?,nationality=?,birth_country=?,birth_city=?,latitude=?,longitude=?,metadata_source=? WHERE id=(SELECT author_id FROM books WHERE id=?)",
                (author, nationality, birth_country, birth_city, latitude, longitude, metadata_source, book.id),
            )
