from app.paths import AppPaths
from database.db import Database
from gutenberg.client import SearchResult
from services.library_service import LibraryService


class FakeGutenbergClient:
    def search(self, query="", *, gutenberg_id=None, timeout=20):
        return [SearchResult(gutenberg_id, f"Online Book {gutenberg_id}", "Remote Author", "en", f"https://example.test/{gutenberg_id}.txt")]

    def download(self, result, timeout=60):
        return ("abcdefghijklmnopqrstuvwxyz0123456789 " * 20).encode()


def test_online_corpus_auto_provision(tmp_path):
    paths = AppPaths(tmp_path, tmp_path / "books", tmp_path / "cache", tmp_path / "indexes", tmp_path / "database", tmp_path / "logs", tmp_path / "keys")
    for path in paths.__dict__.values():
        path.mkdir(parents=True, exist_ok=True)
    db = Database(paths.database / "library.sqlite3")
    ready = LibraryService(db, paths).ensure_online_corpus(3, client=FakeGutenbergClient())
    assert len(ready) >= 3
    assert all(book.metadata_ready and book.indexed for book in ready)

