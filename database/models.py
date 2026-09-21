from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    id: int
    gutenberg_id: int | None
    title: str
    author: str
    nationality: str
    birth_country: str
    birth_city: str
    latitude: float | None
    longitude: float | None
    local_path: str
    sha256: str
    blake3: str
    normalization_version: int
    indexed: bool = True
    language: str = "UNKNOWN"

    @property
    def external_id(self) -> int:
        return self.gutenberg_id if self.gutenberg_id is not None else -self.id

    @property
    def metadata_ready(self) -> bool:
        values = (self.nationality, self.birth_country, self.birth_city)
        return all(v and v != "UNKNOWN" for v in values) and self.latitude is not None and self.longitude is not None

