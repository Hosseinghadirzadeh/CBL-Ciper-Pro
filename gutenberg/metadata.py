from dataclasses import asdict

from gutenberg.client import SearchResult


def as_metadata(result: SearchResult) -> dict:
    return asdict(result)

