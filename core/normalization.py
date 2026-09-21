from __future__ import annotations

import unicodedata

from app.constants import NORMALIZATION_VERSION


def normalize_character(char: str) -> str:
    """Return a searchable unit or an empty string for non-corpus symbols."""
    normalized = unicodedata.normalize("NFC", char).casefold()
    return normalized if len(normalized) == 1 and normalized.isalnum() else ""


def normalize_corpus(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def normalize_word(word: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFC", word).casefold() if ch.isalnum())

