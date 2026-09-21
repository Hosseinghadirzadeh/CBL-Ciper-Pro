from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import blake3

from app.paths import AppPaths
from database.db import Database
from indexing.book_indexer import index_book
from gutenberg.client import GutenbergClient
from gutenberg.initial_corpus import STARTER_CORPUS


class LibraryService:
    def __init__(self, db: Database, paths: AppPaths):
        self.db, self.paths = db, paths

    def import_text(self, source: str | Path, *, title: str, author: str, gutenberg_id: int | None = None, language: str = "UNKNOWN", nationality: str = "UNKNOWN", birth_country: str = "UNKNOWN", birth_city: str = "UNKNOWN", latitude: float | None = None, longitude: float | None = None, metadata_source: str = "user") -> int:
        source = Path(source)
        raw = source.read_bytes()
        raw.decode("utf-8")
        stem = f"pg{gutenberg_id}" if gutenberg_id else hashlib.sha256(raw).hexdigest()[:16]
        destination = self.paths.books / f"{stem}.txt"
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
        book_id = self.db.add_book(gutenberg_id=gutenberg_id, title=title, author=author, local_path=str(destination), sha256=hashlib.sha256(raw).hexdigest(), blake3=blake3.blake3(raw).hexdigest(), language=language, nationality=nationality, birth_country=birth_country, birth_city=birth_city, latitude=latitude, longitude=longitude, metadata_source=metadata_source)
        index_book(self.db, book_id)
        return book_id

    def ensure_online_corpus(self, required_count: int, *, client: GutenbergClient | None = None, progress=None) -> list:
        """Download and index enough curated Gutenberg books for CBL-GEO.

        The public books come from the internet; encryption and passwords remain
        on the user's computer. Downloads are cached for later offline use.
        """
        if not 2 <= required_count <= 8:
            raise ValueError("Books per symbol must be between 2 and 8")
        client = client or GutenbergClient()
        ready = self.db.books(ready_only=True)
        if len(ready) >= required_count:
            return ready
        for profile in STARTER_CORPUS:
            if len(self.db.books(ready_only=True)) >= required_count:
                break
            gid = profile["gutenberg_id"]
            existing = self.db.book_by_external_id(gid)
            if existing is not None:
                metadata = {k: profile[k] for k in ("author", "nationality", "birth_country", "birth_city", "latitude", "longitude")}
                self.db.update_book_metadata(gid, **metadata, metadata_source="curated starter metadata v1")
                if not existing.indexed:
                    index_book(self.db, existing.id)
            else:
                try:
                    if hasattr(client, "download_by_id"):
                        raw = client.download_by_id(gid)
                        title, language = profile["title"], profile["language"]
                    else:
                        result = client.search(gutenberg_id=gid)[0]
                        raw = client.download(result)
                        title, language = result.title, result.language
                except Exception as exc:
                    raise RuntimeError("Could not download the online Gutenberg corpus. Check your internet connection and try again.") from exc
                cache_path = self.paths.cache / f"pg{gid}.txt"
                cache_path.write_bytes(raw)
                self.import_text(cache_path, title=title, author=profile["author"], gutenberg_id=gid, language=language, nationality=profile["nationality"], birth_country=profile["birth_country"], birth_city=profile["birth_city"], latitude=profile["latitude"], longitude=profile["longitude"], metadata_source="Project Gutenberg text + curated starter metadata v1")
            if progress:
                progress(min(35, int(len(self.db.books(ready_only=True)) * 35 / required_count)))
        ready = self.db.books(ready_only=True)
        if len(ready) < required_count:
            raise RuntimeError(f"The online corpus could provide only {len(ready)} of {required_count} required books.")
        return ready
