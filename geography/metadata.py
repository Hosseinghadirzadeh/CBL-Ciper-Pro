from dataclasses import dataclass


@dataclass(frozen=True)
class GeographicMetadata:
    country: str
    city: str
    latitude: float
    longitude: float
    source: str

