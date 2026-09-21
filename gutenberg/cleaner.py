from __future__ import annotations

import re


START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I)
END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I)


def strip_boilerplate(text: str) -> str:
    start = START.search(text)
    end = END.search(text)
    begin = start.end() if start else 0
    finish = end.start() if end and end.start() > begin else len(text)
    return text[begin:finish].strip()

