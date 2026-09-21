from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    books: Path
    cache: Path
    indexes: Path
    database: Path
    logs: Path
    keys: Path

    @classmethod
    def discover(cls, portable: bool | None = None) -> "AppPaths":
        executable_dir = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(sys.argv[0]).resolve().parent)
        portable = ("--portable" in sys.argv) if portable is None else portable
        if portable:
            root = executable_dir / "portable_data"
        else:
            root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "CBL Ciper Pro"
        result = cls(root, root / "books", root / "cache", root / "indexes", root / "database", root / "logs", root / "keys")
        for path in result.__dict__.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        return result
