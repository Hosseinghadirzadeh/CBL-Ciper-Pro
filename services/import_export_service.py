from __future__ import annotations

import io
import zipfile
from pathlib import Path


def pack_folder(folder: str | Path) -> bytes:
    folder = Path(folder).resolve()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(folder).as_posix())
    return stream.getvalue()


def unpack_folder(data: bytes, destination: str | Path) -> None:
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError("Unsafe path in encrypted folder archive")
        archive.extractall(destination)

