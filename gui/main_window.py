from __future__ import annotations

import base64
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSpinBox, QStackedWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.constants import APP_NAME
from crypto.hashing import ALGORITHMS, hash_bytes, hash_file
from crypto.signatures import generate_keypair, sign, verify
from database.db import Database
from gutenberg.client import GutenbergClient
from gui.workers import Worker
from services.decryption_service import DecryptionService
from services.encryption_service import EncryptionService
from services.library_service import LibraryService
from version import __version__


STYLE = """
* { font-family:'Segoe UI'; }
QWidget { background:#09111f; color:#e8eef8; font-size:13px; }
QLabel { background:transparent; }
QMainWindow { background:#07101d; }
QWidget#shell { background:#07101d; }
QFrame#sidebar { background:#0b1526; border-right:1px solid #20304a; }
QFrame#topbar { background:#0b1526; border-bottom:1px solid #20304a; }
QLabel#brand { color:#f8fbff; font-size:18px; font-weight:700; }
QLabel#eyebrow { color:#62d8ff; font-size:11px; font-weight:700; letter-spacing:1px; }
QLabel#pageTitle { color:#f8fbff; font-size:26px; font-weight:700; }
QLabel#muted { color:#8fa3bf; }
QLabel#algorithmPill { background:#113152; color:#72ddff; border:1px solid #1e6c96; border-radius:14px; padding:6px 12px; font-weight:700; }
QLabel#securePill { background:#0f372e; color:#68e2ba; border:1px solid #1a765e; border-radius:14px; padding:6px 12px; font-weight:700; }
QListWidget { background:transparent; border:0; outline:0; padding:6px; font-size:14px; }
QListWidget::item { color:#9fb0c8; padding:12px 14px; margin:2px 0; border-radius:8px; }
QListWidget::item:hover { background:#12233b; color:#edf6ff; }
QListWidget::item:selected { background:#153b63; color:#7fe2ff; border-left:3px solid #3bc8ff; }
QFrame#card { background:#101d30; border:1px solid #243750; border-radius:12px; }
QFrame#heroCard { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #102d4b,stop:0.55 #123052,stop:1 #123a3d); border:1px solid #286184; border-radius:16px; }
QFrame#metricCard { background:#0f1c2d; border:1px solid #22354d; border-radius:11px; }
QFrame#pipelineCard { background:#0c1a2c; border:1px solid #285173; border-radius:12px; }
QLabel#metricValue { color:#f8fbff; font-size:28px; font-weight:700; }
QLabel#metricLabel { color:#8fa3bf; font-size:12px; }
QLabel#stepNumber { background:#174d70; color:#77ddff; border-radius:16px; padding:6px; font-weight:700; }
QLabel#stepTitle { color:#f2f7ff; font-size:14px; font-weight:700; }
QLabel#stepBody { color:#92a7c2; font-size:11px; }
QLabel#arrow { color:#48c9ff; font-size:23px; font-weight:700; }
QLineEdit,QPlainTextEdit,QTableWidget,QComboBox,QSpinBox { background:#0a1423; border:1px solid #314762; border-radius:7px; padding:8px; selection-background-color:#226a99; }
QLineEdit:focus,QPlainTextEdit:focus,QComboBox:focus,QSpinBox:focus { border:1px solid #3bc8ff; }
QHeaderView::section { background:#13233a; color:#a9bdd5; border:0; border-bottom:1px solid #314762; padding:8px; font-weight:600; }
QTableWidget { gridline-color:#1d3048; }
QPushButton { background:#1777b5; color:white; border:0; border-radius:7px; padding:10px 16px; font-weight:650; }
QPushButton:hover { background:#2297d6; } QPushButton:pressed { background:#126393; } QPushButton:disabled { background:#35465c; color:#8292a8; }
QPushButton#secondary { background:#16283e; border:1px solid #34506e; }
QPushButton#secondary:hover { background:#1d3856; }
QProgressBar { border:1px solid #314762; border-radius:6px; text-align:center; background:#091321; min-height:13px; }
QProgressBar::chunk { background:#25c38f; border-radius:5px; }
QScrollBar:vertical { background:#0a1423; width:10px; } QScrollBar::handle:vertical { background:#36506d; border-radius:5px; min-height:30px; }
"""


class BasePage(QWidget):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.layout = QVBoxLayout(self)
        heading = QLabel(title); heading.setObjectName("pageTitle")
        self.layout.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle); note.setWordWrap(True); note.setObjectName("muted")
            self.layout.addWidget(note)
        self.layout.addSpacing(8)

    def card(self):
        frame = QFrame(); frame.setObjectName("card"); frame.setLayout(QVBoxLayout())
        self.layout.addWidget(frame)
        return frame.layout()


class MetricCard(QFrame):
    def __init__(self, value: str, label: str, accent: str = "#6fdcff"):
        super().__init__(); self.setObjectName("metricCard")
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 14, 16, 14)
        self.value = QLabel(value); self.value.setObjectName("metricValue"); self.value.setStyleSheet(f"color:{accent}")
        caption = QLabel(label); caption.setObjectName("metricLabel")
        layout.addWidget(self.value); layout.addWidget(caption)


class PipelineStep(QFrame):
    def __init__(self, number: str, title: str, body: str, accent: str = "#48c9ff"):
        super().__init__(); self.setObjectName("pipelineCard"); self.setMinimumWidth(145)
        layout = QVBoxLayout(self); layout.setContentsMargins(14, 14, 14, 14); layout.setSpacing(7)
        badge = QLabel(number); badge.setObjectName("stepNumber"); badge.setFixedSize(34, 34); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); badge.setStyleSheet(f"background:{accent}22;color:{accent};border:1px solid {accent}66;border-radius:17px;font-weight:700")
        heading = QLabel(title); heading.setObjectName("stepTitle"); heading.setWordWrap(True)
        description = QLabel(body); description.setObjectName("stepBody"); description.setWordWrap(True)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignLeft); layout.addWidget(heading); layout.addWidget(description); layout.addStretch()


def add_pipeline(layout, compact: bool = False):
    steps = [
        ("1", "Multi-Book", "K literary references\nper symbol", "#49c9ff"),
        ("2", "Nationality", "Author metadata\nderived mask", "#8a8cff"),
        ("3", "Geography", "Birthplace and\ncoordinate mask", "#32d3a0"),
        ("4", "AES-256-GCM", "Confidentiality and\nauthentication", "#f5bc62"),
        ("5", ".LBCX", "Versioned encrypted\ncontainer", "#ff7e9a"),
    ]
    for index, step in enumerate(steps):
        layout.addWidget(PipelineStep(*step), 1)
        if index < len(steps) - 1:
            arrow = QLabel("›"); arrow.setObjectName("arrow"); arrow.setAlignment(Qt.AlignmentFlag.AlignCenter); arrow.setFixedWidth(20); layout.addWidget(arrow)


class DashboardPage(BasePage):
    def __init__(self, db):
        super().__init__("Dashboard", "LBC-GEO security and literary corpus status")
        self.db = db
        hero = QFrame(); hero.setObjectName("heroCard"); hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(24, 20, 24, 20)
        copy = QVBoxLayout(); eyebrow = QLabel("CUSTOM ENCRYPTION ARCHITECTURE"); eyebrow.setObjectName("eyebrow")
        title = QLabel("LBC-GEO v1"); title.setStyleSheet("font-size:30px;font-weight:750;color:#ffffff")
        text = QLabel("A custom reversible Literary, Nationality & Geographic transformation\nsecured by AES-256-GCM."); text.setObjectName("muted")
        copy.addWidget(eyebrow); copy.addWidget(title); copy.addWidget(text)
        brand = QLabel("LBC\nGEO"); brand.setAlignment(Qt.AlignmentFlag.AlignCenter); brand.setFixedSize(105, 105); brand.setStyleSheet("background:#0c2137;color:#64d9ff;border:2px solid #3bc8ff;border-radius:52px;font-size:16px;font-weight:800")
        hero_layout.addLayout(copy, 1); hero_layout.addWidget(brand); self.layout.addWidget(hero)
        metrics = QHBoxLayout(); self.book_metric = MetricCard("0", "Downloaded books"); self.index_metric = MetricCard("0", "Indexed books", "#8e9aff"); self.ready_metric = MetricCard("0", "LBC-GEO ready", "#41d7a4"); self.health_metric = MetricCard("READY", "Security status", "#f5bc62")
        for metric in (self.book_metric, self.index_metric, self.ready_metric, self.health_metric): metrics.addWidget(metric)
        self.layout.addLayout(metrics)
        flow_card = QFrame(); flow_card.setObjectName("card"); flow = QVBoxLayout(flow_card); flow.addWidget(QLabel("Active encryption pipeline", objectName="stepTitle")); pipeline = QHBoxLayout(); add_pipeline(pipeline, True); flow.addLayout(pipeline); self.layout.addWidget(flow_card)
        controls = QHBoxLayout(); self.status = QLabel("Database and cryptographic backends operational"); self.status.setObjectName("muted"); button = QPushButton("Refresh status"); button.setObjectName("secondary"); button.clicked.connect(self.refresh); controls.addWidget(self.status); controls.addStretch(); controls.addWidget(button); self.layout.addLayout(controls); self.layout.addStretch(); self.refresh()

    def refresh(self):
        books = self.db.books()
        self.book_metric.value.setText(str(len(books))); self.index_metric.value.setText(str(sum(b.indexed for b in books))); self.ready_metric.value.setText(str(sum(b.metadata_ready and b.indexed for b in books)))


class AlgorithmPage(BasePage):
    def __init__(self):
        super().__init__("The LBC-GEO Algorithm", "The custom encryption option, shown exactly as it is used by this application.")
        credit = QFrame(); credit.setObjectName("heroCard"); c = QHBoxLayout(credit); c.setContentsMargins(24, 20, 24, 20)
        left = QVBoxLayout(); eyebrow = QLabel("CUSTOM ENCRYPTION OPTION"); eyebrow.setObjectName("eyebrow"); name = QLabel("LBC-GEO v1"); name.setStyleSheet("font-size:24px;font-weight:750;color:#ffffff"); description = QLabel("LBC-GEO combines literary references, author nationality, and geographic coordinates\nas three reversible transformations before established authenticated encryption."); description.setObjectName("muted")
        left.addWidget(eyebrow); left.addWidget(name); left.addWidget(description); c.addLayout(left, 1)
        badge = QLabel("LBC-GEO\nVERSION 1"); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); badge.setFixedSize(120, 90); badge.setStyleSheet("background:#0a1b2e;color:#6edfff;border:1px solid #3bc8ff;border-radius:12px;font-size:16px;font-weight:800"); c.addWidget(badge); self.layout.addWidget(credit)
        label = QLabel("How LBC-GEO transforms data"); label.setObjectName("stepTitle"); label.setStyleSheet("font-size:17px;font-weight:700"); self.layout.addWidget(label)
        pipeline = QHBoxLayout(); add_pipeline(pipeline); self.layout.addLayout(pipeline)
        detail = QFrame(); detail.setObjectName("card"); grid = QGridLayout(detail); grid.setContentsMargins(20, 16, 20, 16)
        details = [
            ("LAYER 1 · LITERARY", "The same symbol is referenced in multiple distinct books using Gutenberg IDs and exact normalized positions."),
            ("LAYER 2 · NATIONALITY", "Author name, nationality, birth country, and birth city derive a unique reversible per-symbol mask."),
            ("LAYER 3 · GEOGRAPHY", "Country code, birthplace, latitude, and longitude derive a second independent reversible mask."),
            ("SECURITY ENVELOPE", "Argon2id + HKDF derive separated keys. AES-256-GCM provides real confidentiality and tamper detection."),
        ]
        for row, (heading, body) in enumerate(details):
            h = QLabel(heading); h.setObjectName("eyebrow"); b = QLabel(body); b.setWordWrap(True); b.setObjectName("muted"); grid.addWidget(h, row, 0); grid.addWidget(b, row, 1)
        self.layout.addWidget(detail); self.layout.addStretch()


class CryptoPage(BasePage):
    def __init__(self, db, paths, encrypting: bool):
        super().__init__("Encrypt with LBC-GEO" if encrypting else "Decrypt LBCX", "LBC-GEO v1 custom transformation, protected by authenticated AES-256-GCM.")
        self.encrypting, self.db = encrypting, db
        self.service = EncryptionService(db) if encrypting else DecryptionService(db)
        self.library_service = LibraryService(db, paths)
        self.pool = QThreadPool.globalInstance()
        algorithm_bar = QFrame(); algorithm_bar.setObjectName("heroCard"); algorithm_layout = QHBoxLayout(algorithm_bar); algorithm_layout.setContentsMargins(18, 13, 18, 13)
        algorithm_copy = QVBoxLayout(); algorithm_label = QLabel("ACTIVE ENCRYPTION OPTION"); algorithm_label.setObjectName("eyebrow"); algorithm_name = QLabel("LBC-GEO v1  ·  Literary + Nationality + Geography"); algorithm_name.setObjectName("stepTitle"); algorithm_copy.addWidget(algorithm_label); algorithm_copy.addWidget(algorithm_name)
        security = QLabel("AES-256-GCM SECURED"); security.setObjectName("securePill"); algorithm_layout.addLayout(algorithm_copy, 1); algorithm_layout.addWidget(security); self.layout.addWidget(algorithm_bar)
        box = self.card(); self.text = QPlainTextEdit(); self.text.setPlaceholderText("Enter plaintext" if encrypting else "Decrypted text appears here")
        self.text.setMinimumHeight(165)
        box.addWidget(self.text)
        form = QFormLayout(); self.algorithm = QComboBox(); self.algorithm.addItem("LBC-GEO v1 — Literary + Nationality + Geography"); self.algorithm.setEnabled(False); form.addRow("Algorithm", self.algorithm)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setPlaceholderText("Never stored or logged"); form.addRow("Password", self.password)
        if encrypting:
            self.confirm = QLineEdit(); self.confirm.setEchoMode(QLineEdit.EchoMode.Password); form.addRow("Confirm", self.confirm)
            self.books = QSpinBox(); self.books.setRange(2, 8); self.books.setValue(3); form.addRow("Books per symbol", self.books)
            self.corpus_mode = QComboBox(); self.corpus_mode.addItem("Online Gutenberg Corpus — automatic download", "online"); self.corpus_mode.addItem("Local Library Only — no downloads", "local"); form.addRow("Literary corpus", self.corpus_mode)
        box.addLayout(form)
        controls = QHBoxLayout(); self.text_button = QPushButton("Encrypt text with LBC-GEO" if encrypting else "Open .lbcx and decrypt"); self.file_button = QPushButton("Encrypt file" if encrypting else "Decrypt file"); self.file_button.setObjectName("secondary")
        controls.addWidget(self.text_button); controls.addWidget(self.file_button); box.addLayout(controls)
        self.progress = QProgressBar(); self.progress.hide(); box.addWidget(self.progress)
        self.status = QLabel(); box.addWidget(self.status); self.layout.addStretch()
        self.text_button.clicked.connect(self.process_text); self.file_button.clicked.connect(self.process_file)

    def _validate(self):
        if not self.password.text(): raise ValueError("Password must not be empty")
        if self.encrypting and self.password.text() != self.confirm.text(): raise ValueError("Passwords do not match")

    def _run(self, function, *args, done=None):
        self.progress.show(); self.progress.setValue(0); self.text_button.setEnabled(False); self.file_button.setEnabled(False)
        worker = Worker(function, *args); worker.signals.progress.connect(self.progress.setValue)
        worker.signals.error.connect(lambda message: QMessageBox.critical(self, "LBC Cipher Pro", message))
        if done: worker.signals.result.connect(done)
        worker.signals.finished.connect(lambda: (self.text_button.setEnabled(True), self.file_button.setEnabled(True), self.progress.setValue(100)))
        self.pool.start(worker)

    def process_text(self):
        try: self._validate()
        except ValueError as exc: return QMessageBox.warning(self, APP_NAME, str(exc))
        if self.encrypting:
            target, _ = QFileDialog.getSaveFileName(self, "Save encrypted text", "message.lbcx", "LBCX (*.lbcx)")
            if target:
                self.status.setText("Connecting to Project Gutenberg and preparing the online corpus…" if self.corpus_mode.currentData() == "online" else "Preparing local corpus…")
                def job(progress=None):
                    if self.corpus_mode.currentData() == "online": self.library_service.ensure_online_corpus(self.books.value(), progress=progress)
                    Path(target).write_bytes(self.service.encrypt_bytes(self.text.toPlainText().encode(), self.password.text(), text=True, books_per_symbol=self.books.value(), progress=progress)); return target
                self._run(job, done=lambda path: self.status.setText(f"✓ Encrypted with LBC-GEO v1 → AES-256-GCM\n{path}"))
        else:
            source, _ = QFileDialog.getOpenFileName(self, "Open encrypted text", "", "LBCX (*.lbcx)")
            if source:
                self._run(lambda progress=None: self.service.decrypt_bytes(Path(source).read_bytes(), self.password.text(), progress=progress)[0].decode("utf-8"), done=lambda value: self.text.setPlainText(value))

    def process_file(self):
        try: self._validate()
        except ValueError as exc: return QMessageBox.warning(self, APP_NAME, str(exc))
        if self.encrypting:
            source, _ = QFileDialog.getOpenFileName(self, "Select file")
            if not source: return
            target, _ = QFileDialog.getSaveFileName(self, "Save encrypted file", source + ".lbcx", "LBCX (*.lbcx)")
            if target:
                self.status.setText("Connecting to Project Gutenberg and preparing the online corpus…" if self.corpus_mode.currentData() == "online" else "Preparing local corpus…")
                def job(progress=None):
                    if self.corpus_mode.currentData() == "online": self.library_service.ensure_online_corpus(self.books.value(), progress=progress)
                    self.service.encrypt_file(source, target, self.password.text(), self.books.value(), progress=progress)
                self._run(job, done=lambda _: self.status.setText(f"✓ Algorithm used: LBC-GEO v1 → AES-256-GCM\n{target}"))
        else:
            source, _ = QFileDialog.getOpenFileName(self, "Select LBCX", "", "LBCX (*.lbcx)")
            if not source: return
            suggested = source[:-5] if source.lower().endswith(".lbcx") else source + ".decrypted"
            target, _ = QFileDialog.getSaveFileName(self, "Save decrypted file", suggested)
            if target: self._run(self.service.decrypt_file, source, target, self.password.text(), done=lambda _: self.status.setText(f"✓ Reversed: AES-256-GCM → Geography → Nationality → Multi-Book\n{target}"))


class LibraryPage(BasePage):
    def __init__(self, db, paths):
        super().__init__("Library", "Import UTF-8 books or search Project Gutenberg. Complete metadata is required for LBC-GEO.")
        self.db, self.paths, self.service, self.client = db, paths, LibraryService(db, paths), GutenbergClient(); self.pool = QThreadPool.globalInstance(); self.results = []
        controls = QHBoxLayout(); self.query = QLineEdit(); self.query.setPlaceholderText("Title, author, or Gutenberg ID"); search = QPushButton("Search Gutenberg"); download = QPushButton("Download selected"); local = QPushButton("Import local TXT")
        controls.addWidget(self.query); controls.addWidget(search); controls.addWidget(download); controls.addWidget(local); self.layout.addLayout(controls)
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["ID", "Title", "Author", "Language", "Ready", "Source"]); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.horizontalHeader().setStretchLastSection(True); self.layout.addWidget(self.table)
        self.status = QLabel(); self.layout.addWidget(self.status); search.clicked.connect(self.search); download.clicked.connect(self.download); local.clicked.connect(self.import_local); self.refresh()

    def refresh(self):
        books = self.db.books(); self.table.setRowCount(len(books))
        for row, book in enumerate(books):
            values = [book.external_id, book.title, book.author, book.language, "YES" if book.metadata_ready and book.indexed else "NO", "Local library"]
            for col, value in enumerate(values): self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def _worker(self, func, done):
        worker = Worker(func); worker.signals.result.connect(done); worker.signals.error.connect(lambda e: QMessageBox.critical(self, APP_NAME, e)); self.pool.start(worker)

    def search(self):
        query = self.query.text().strip(); gid = int(query) if query.isdigit() else None
        self.status.setText("Searching…")
        self._worker(lambda progress=None: self.client.search("" if gid else query, gutenberg_id=gid), self.show_results)

    def show_results(self, results):
        self.results = results; self.table.setRowCount(len(results))
        for row, result in enumerate(results):
            for col, value in enumerate([result.gutenberg_id, result.title, result.author, result.language, "metadata needed", "Project Gutenberg"]): self.table.setItem(row, col, QTableWidgetItem(str(value)))
        self.status.setText(f"{len(results)} result(s)")

    def download(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.results): return QMessageBox.information(self, APP_NAME, "Search and select a Gutenberg result first.")
        result = self.results[row]
        def job(progress=None):
            raw = self.client.download(result); path = self.paths.cache / f"pg{result.gutenberg_id}.txt"; path.write_bytes(raw)
            return self.service.import_text(path, title=result.title, author=result.author, gutenberg_id=result.gutenberg_id, language=result.language, metadata_source="Gutenberg; supplemental metadata UNKNOWN")
        self._worker(job, lambda _: (self.refresh(), self.status.setText("Downloaded and indexed. Add author metadata before encryption.")))

    def import_local(self):
        source, _ = QFileDialog.getOpenFileName(self, "Import UTF-8 text", "", "Text (*.txt)")
        if not source: return
        fields = []
        for label, default in [("Title", Path(source).stem), ("Author", "UNKNOWN"), ("Nationality", "UNKNOWN"), ("Birth country", "UNKNOWN"), ("Birth city", "UNKNOWN"), ("Latitude", ""), ("Longitude", "")]:
            value, ok = QInputDialog.getText(self, label, label, text=default)
            if not ok: return
            fields.append(value)
        try:
            self.service.import_text(source, title=fields[0], author=fields[1], nationality=fields[2], birth_country=fields[3], birth_city=fields[4], latitude=float(fields[5]) if fields[5] else None, longitude=float(fields[6]) if fields[6] else None)
            self.refresh()
        except Exception as exc: QMessageBox.critical(self, APP_NAME, str(exc))


class HashPage(BasePage):
    def __init__(self):
        super().__init__("Hash", "Calculate and compare standard cryptographic digests.")
        box = self.card(); self.algorithm = QComboBox(); self.algorithm.addItems([*ALGORITHMS, "BLAKE3"]); self.input = QPlainTextEdit(); self.input.setPlaceholderText("Text to hash"); self.output = QLineEdit(); self.output.setReadOnly(True)
        buttons = QHBoxLayout(); text_btn = QPushButton("Hash text"); file_btn = QPushButton("Hash file"); copy_btn = QPushButton("Copy"); buttons.addWidget(text_btn); buttons.addWidget(file_btn); buttons.addWidget(copy_btn)
        for widget in (self.algorithm, self.input, self.output): box.addWidget(widget)
        box.addLayout(buttons); self.layout.addStretch(); text_btn.clicked.connect(lambda: self.output.setText(hash_bytes(self.input.toPlainText().encode(), self.algorithm.currentText())))
        def file_hash():
            path, _ = QFileDialog.getOpenFileName(self, "Hash file")
            if path: self.output.setText(hash_file(path, self.algorithm.currentText()))
        file_btn.clicked.connect(file_hash); copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.output.text()))


class KeysPage(BasePage):
    def __init__(self):
        super().__init__("Keys", "Generate password-encrypted Ed25519 private keys. Private keys are never written unencrypted.")
        box = self.card(); self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); button = QPushButton("Generate and export keypair"); box.addWidget(QLabel("Private-key password")); box.addWidget(self.password); box.addWidget(button); self.layout.addStretch(); button.clicked.connect(self.generate)

    def generate(self):
        if not self.password.text(): return QMessageBox.warning(self, APP_NAME, "Enter a key password")
        path, _ = QFileDialog.getSaveFileName(self, "Save encrypted private key", "ed25519-private.lbckey", "LBC key (*.lbckey)")
        if not path: return
        private, public = generate_keypair(self.password.text()); Path(path).write_bytes(private); Path(path + ".pub").write_text(base64.b64encode(public).decode(), encoding="ascii"); QMessageBox.information(self, APP_NAME, "Encrypted private key and public key exported.")


class SignaturesPage(BasePage):
    def __init__(self):
        super().__init__("Signatures", "Ed25519 signatures prove origin and integrity; they do not encrypt data.")
        box = self.card(); sign_btn = QPushButton("Sign file"); verify_btn = QPushButton("Verify file signature"); box.addWidget(sign_btn); box.addWidget(verify_btn); self.result = QLabel(); box.addWidget(self.result); self.layout.addStretch(); sign_btn.clicked.connect(self.sign_file); verify_btn.clicked.connect(self.verify_file)

    def sign_file(self):
        source, _ = QFileDialog.getOpenFileName(self, "File to sign"); key, _ = QFileDialog.getOpenFileName(self, "Encrypted private key", "", "LBC key (*.lbckey)")
        if not source or not key: return
        password, ok = QInputDialog.getText(self, "Key password", "Password", QLineEdit.EchoMode.Password)
        if not ok: return
        try: Path(source + ".sig").write_bytes(sign(Path(source).read_bytes(), Path(key).read_bytes(), password)); self.result.setText("Signature written: " + source + ".sig")
        except Exception: QMessageBox.critical(self, APP_NAME, "Incorrect key password or invalid private key.")

    def verify_file(self):
        source, _ = QFileDialog.getOpenFileName(self, "Signed file"); signature, _ = QFileDialog.getOpenFileName(self, "Signature", "", "Signature (*.sig)"); public, _ = QFileDialog.getOpenFileName(self, "Public key", "", "Public key (*.pub)")
        if source and signature and public:
            valid = verify(Path(source).read_bytes(), Path(signature).read_bytes(), base64.b64decode(Path(public).read_text().strip()))
            self.result.setText("VALID" if valid else "INVALID"); self.result.setStyleSheet("color:#10b981;font-size:20px;font-weight:bold" if valid else "color:#ef4444;font-size:20px;font-weight:bold")


class InfoPage(BasePage):
    def __init__(self, title, text):
        super().__init__(title); label = QLabel(text); label.setWordWrap(True); label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); self.card().addWidget(label); self.layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, db: Database, paths):
        super().__init__(); self.setWindowTitle(f"LBC Cipher Pro {__version__} — LBC-GEO"); self.resize(1280, 820); self.setMinimumSize(1040, 680); self.setStyleSheet(STYLE)
        import sys
        root_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        icon_path = root_path / "resources" / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        root = QWidget(); root.setObjectName("shell"); shell = QHBoxLayout(root); shell.setContentsMargins(0, 0, 0, 0); shell.setSpacing(0)
        sidebar_frame = QFrame(); sidebar_frame.setObjectName("sidebar"); sidebar_frame.setFixedWidth(230); sidebar_layout = QVBoxLayout(sidebar_frame); sidebar_layout.setContentsMargins(14, 18, 14, 16)
        brand_row = QHBoxLayout(); logo = QLabel(); logo_path = root_path / "resources" / "app.png"
        if logo_path.exists(): logo.setPixmap(QPixmap(str(logo_path)).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        brand_copy = QVBoxLayout(); brand = QLabel("LBC Cipher Pro"); brand.setObjectName("brand"); version = QLabel(f"VERSION {__version__}"); version.setObjectName("eyebrow"); brand_copy.addWidget(brand); brand_copy.addWidget(version); brand_row.addWidget(logo); brand_row.addLayout(brand_copy); sidebar_layout.addLayout(brand_row); sidebar_layout.addSpacing(18)
        navigation = QLabel("NAVIGATION"); navigation.setObjectName("eyebrow"); sidebar_layout.addWidget(navigation)
        self.sidebar = QListWidget(); sidebar_layout.addWidget(self.sidebar, 1)
        credit = QFrame(); credit.setObjectName("metricCard"); credit_layout = QVBoxLayout(credit); credit_layout.setContentsMargins(12, 11, 12, 11); credit_label = QLabel("CUSTOM ENCRYPTION"); credit_label.setObjectName("eyebrow"); option = QLabel("LBC-GEO v1\nEnabled"); option.setStyleSheet("font-weight:700;color:#eaf6ff"); credit_layout.addWidget(credit_label); credit_layout.addWidget(option); sidebar_layout.addWidget(credit)
        content = QWidget(); content_layout = QVBoxLayout(content); content_layout.setContentsMargins(0, 0, 0, 0); content_layout.setSpacing(0)
        topbar = QFrame(); topbar.setObjectName("topbar"); top = QHBoxLayout(topbar); top.setContentsMargins(24, 13, 24, 13); suite = QLabel("LITERARY · NATIONALITY · GEOGRAPHIC CRYPTOGRAPHIC SYSTEM"); suite.setObjectName("muted"); algorithm = QLabel("LBC-GEO v1"); algorithm.setObjectName("algorithmPill"); secure = QLabel("AES-256-GCM SECURED"); secure.setObjectName("securePill"); top.addWidget(suite); top.addStretch(); top.addWidget(algorithm); top.addWidget(secure); content_layout.addWidget(topbar)
        self.stack = QStackedWidget(); self.stack.setContentsMargins(22, 18, 22, 18); content_layout.addWidget(self.stack, 1)
        pages = [DashboardPage(db), AlgorithmPage(), CryptoPage(db, paths, True), CryptoPage(db, paths, False), LibraryPage(db, paths), KeysPage(), HashPage(), SignaturesPage(), InfoPage("History", "History is disabled by default to minimize metadata retention."), InfoPage("Settings", "Defaults: online Gutenberg corpus, LBC-GEO v1, AES-256-GCM, three books per symbol, and automatic corpus verification. Use --portable to store data next to the executable."), InfoPage("About", "LBC Cipher Pro 1.0.0\n\nLBC-GEO v1 is a custom reversible Literary, Nationality & Geographic transformation available as an encryption option. Public-domain books are downloaded from Project Gutenberg; plaintext and passwords remain on this computer.\n\nLBC-GEO itself is experimental—not a substitute for modern cryptography. Confidentiality and authentication are provided by AES-256-GCM with Argon2id and HKDF.\n\nPassword loss is permanent. The application contains no recovery backdoor. Secure deletion cannot be guaranteed, especially on SSDs.")]
        names = ["Dashboard", "LBC-GEO Algorithm", "Encrypt", "Decrypt", "Library", "Keys", "Hash", "Signatures", "History", "Settings", "About"]
        for name, page in zip(names, pages): self.sidebar.addItem(name); self.stack.addWidget(page)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex); self.sidebar.setCurrentRow(0); shell.addWidget(sidebar_frame); shell.addWidget(content, 1); self.setCentralWidget(root)
