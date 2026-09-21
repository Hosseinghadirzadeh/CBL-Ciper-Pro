from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus
import re
import xml.etree.ElementTree as ET

import requests


USER_AGENT = "LBC-Cipher-Pro/1.0 (Project Gutenberg client)"


@dataclass(frozen=True)
class SearchResult:
    gutenberg_id: int
    title: str
    author: str
    language: str
    text_url: str | None


class GutenbergClient:
    """Searches official Project Gutenberg OPDS and downloads UTF-8 texts."""
    OPDS_SEARCH = "https://www.gutenberg.org/ebooks/search.opds/"

    def search(self, query: str = "", *, gutenberg_id: int | None = None, timeout: int = 20) -> list[SearchResult]:
        url = f"https://www.gutenberg.org/ebooks/{gutenberg_id}.opds" if gutenberg_id else f"{self.OPDS_SEARCH}?query={quote_plus(query)}"
        try:
            response = requests.get(url, timeout=max(timeout, 30), headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            return self.parse_opds(response.content)
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            raise ConnectionError("Project Gutenberg search is temporarily unavailable. Check your internet connection and try again.") from exc

    @staticmethod
    def parse_opds(data: bytes) -> list[SearchResult]:
        atom = "{http://www.w3.org/2005/Atom}"
        root = ET.fromstring(data)
        entries = [root] if root.tag == atom + "entry" else root.findall(".//" + atom + "entry")
        results, seen = [], set()
        for entry in entries:
            id_text = entry.findtext(atom + "id", "")
            match = re.search(r"/ebooks/(\d+)(?:\.opds)?$", id_text) or re.search(r"urn:gutenberg:(\d+)(?::|$)", id_text)
            if not match:
                continue
            gid = int(match.group(1))
            if gid in seen:
                continue
            seen.add(gid)
            title = entry.findtext(atom + "title", "Untitled").strip()
            author = entry.findtext(atom + "content", "").strip()
            if not author:
                author = entry.findtext(atom + "author/" + atom + "name", "UNKNOWN").strip() or "UNKNOWN"
            text_url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
            results.append(SearchResult(gid, title, author, "UNKNOWN", text_url))
        return results

    def download(self, result: SearchResult, timeout: int = 60) -> bytes:
        if not result.text_url:
            raise ValueError("No plain-text edition is available for this book")
        response = requests.get(result.text_url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        content = response.content
        content.decode("utf-8")
        return content

    def download_by_id(self, gutenberg_id: int, timeout: int = 120) -> bytes:
        """Download a known book directly from official Gutenberg mirrors."""
        urls = [
            f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt",
            f"https://www.gutenberg.org/files/{gutenberg_id}/{gutenberg_id}-0.txt",
            f"https://www.gutenberg.org/files/{gutenberg_id}/{gutenberg_id}.txt",
        ]
        last_error = None
        for url in urls:
            try:
                response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                content = response.content
                content.decode("utf-8-sig")
                return content
            except requests.RequestException as exc:
                last_error = exc
        if last_error:
            raise last_error
        raise ValueError(f"No UTF-8 text edition found for Gutenberg book {gutenberg_id}")
