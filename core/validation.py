from __future__ import annotations

import hashlib
from pathlib import Path

from core.errors import CorpusError, MetadataError
from database.models import Book


def require_ready_books(books: list[Book], minimum: int) -> None:
    if len(books) < minimum:
        raise MetadataError(f"At least {minimum} indexed books with complete author and geographic metadata are required.")


def verify_book(book: Book) -> None:
    path = Path(book.local_path)
    if not path.is_file():
        raise CorpusError(f"Required literary corpus book is missing: {book.title}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != book.sha256:
        raise CorpusError("Required literary corpus does not match the encrypted data.")

