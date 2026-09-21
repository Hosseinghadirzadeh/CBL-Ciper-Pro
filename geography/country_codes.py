from __future__ import annotations

_CODES = {"united kingdom": "GB", "england": "GB", "scotland": "GB", "united states": "US", "usa": "US", "france": "FR", "germany": "DE", "iran": "IR", "japan": "JP", "china": "CN", "russia": "RU", "ireland": "IE", "italy": "IT", "spain": "ES"}


def country_code(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) == 2:
        return cleaned.upper()
    return _CODES.get(cleaned.casefold(), "ZZ")

