from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from app.paths import AppPaths
from database.db import Database


def create_context():
    paths = AppPaths.discover()
    logging.basicConfig(filename=paths.logs / "application.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return paths, Database(paths.database / "library.sqlite3")


def load_app_font(app) -> None:
    """Load the Windows UI font explicitly for reliable frozen rendering."""
    from PySide6.QtGui import QFont, QFontDatabase
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for filename in ("segoeui.ttf", "seguisb.ttf", "segoeuib.ttf"):
        path = fonts_dir / filename
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    app.setFont(QFont("Segoe UI", 10))


def run() -> int:
    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow
    app = QApplication(sys.argv)
    app.setApplicationName("LBC Cipher Pro")
    load_app_font(app)
    paths, db = create_context()
    window = MainWindow(db, paths)
    window.show()
    return app.exec()
