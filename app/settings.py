from dataclasses import dataclass


@dataclass
class Settings:
    theme: str = "dark"
    cipher: str = "AES-256-GCM"
    books_per_symbol: int = 3
    nationality_diversity: bool = True
    history_enabled: bool = False
    verify_corpus: bool = True

