# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project = Path(SPECPATH).resolve().parent
datas = [
    (str(project / "database" / "schema.sql"), "database"),
    (str(project / "LICENSE"), "."),
    (str(project / "resources" / "app.ico"), "resources"),
    (str(project / "resources" / "app.png"), "resources"),
]
icon = project / "resources" / "app.ico"

a = Analysis(
    [str(project / "main.py")],
    pathex=[str(project)],
    binaries=[],
    datas=datas,
    hiddenimports=["argon2.low_level", "blake3", "nacl", "cryptography.hazmat.bindings._rust"],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="CBL_Ciper_Pro", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=True, console=False,
    icon=str(icon) if icon.exists() else None,
    version=str(project / "build" / "version_info.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, upx_exclude=[], name="CBL_Ciper_Pro")
