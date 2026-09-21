from __future__ import annotations

import re

from core.normalization import normalize_word


def build_word_index(text: str) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for index, match in enumerate(re.finditer(r"\w+", text, re.UNICODE)):
        word = normalize_word(match.group())
        if word:
            result.setdefault(word, []).append(index)
    return result

