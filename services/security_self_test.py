from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import blake3

from app.application import create_context
from core.errors import AuthenticationError, CorpusError
from crypto.aes_engine import decrypt, encrypt
from crypto.hkdf_engine import separate_keys
from crypto.password_kdf import derive_root_key
from crypto.signatures import generate_keypair, sign, verify
from database.db import Database
from indexing.book_indexer import index_book
from services.decryption_service import DecryptionService
from services.encryption_service import EncryptionService


def run_security_self_test() -> tuple[bool, dict]:
    paths, db = create_context()
    checks: dict[str, bool] = {}
    try:
        root = derive_root_key("LBC self-test password", b"0123456789abcdef")
        checks["argon2id"] = len(root) == 32
        keys = separate_keys(root)
        checks["hkdf_key_separation"] = len(set(keys.values())) == len(keys)
        nonce = os.urandom(12); aad = b"self-test"; message = b"LBC Cipher Pro"
        checks["aes_256_gcm"] = decrypt(keys["aes"], nonce, encrypt(keys["aes"], nonce, message, aad), aad) == message
        checks["secure_random"] = os.urandom(32) != os.urandom(32)
        with db.session() as connection:
            checks["sqlite"] = connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        checks["sha_algorithms"] = hashlib.sha3_512(message).digest() != hashlib.sha256(message).digest()
        checks["blake3"] = len(blake3.blake3(message).digest()) == 32
        private, public = generate_keypair("self-test key password")
        signature = sign(message, private, "self-test key password")
        checks["ed25519"] = verify(message, signature, public)
        checks["book_index_integrity"] = all(book.indexed for book in db.books())
        with tempfile.TemporaryDirectory(dir=paths.cache) as temp_name:
            temp = Path(temp_name)
            test_db = Database(temp / "self-test.sqlite3")
            corpus = ("abcdefghijklmnopqrstuvwxyz0123456789" * 12).encode()
            rows = [
                (1342, "Jane Austen", "British", "England", "Steventon", 51.239, -1.105),
                (1661, "Arthur Conan Doyle", "British", "Scotland", "Edinburgh", 55.9533, -3.1883),
                (2701, "Herman Melville", "American", "United States", "New York", 40.7128, -74.006),
            ]
            for gid, author, nationality, country, city, latitude, longitude in rows:
                book_path = temp / f"{gid}.txt"
                book_path.write_bytes(corpus)
                book_id = test_db.add_book(gutenberg_id=gid, title=f"Self-test {gid}", author=author, local_path=str(book_path), sha256=hashlib.sha256(corpus).hexdigest(), blake3=blake3.blake3(corpus).hexdigest(), nationality=nationality, birth_country=country, birth_city=city, latitude=latitude, longitude=longitude)
                index_book(test_db, book_id)
            encryption, decryption = EncryptionService(test_db), DecryptionService(test_db)
            password = "packaged executable self-test"
            for name, sample in {"lbc_ascii": "Hello World!", "lbc_persian": "سلام، حالت چطوره؟", "lbc_unicode": "Hello 🌍 🔐"}.items():
                container = encryption.encrypt_bytes(sample.encode(), password, text=True)
                checks[name] = decryption.decrypt_bytes(container, password)[0].decode() == sample
            binary = bytes(range(256))
            binary_container = encryption.encrypt_bytes(binary, password)
            checks["lbc_binary"] = decryption.decrypt_bytes(binary_container, password)[0] == binary
            try:
                decryption.decrypt_bytes(binary_container, "wrong password")
                checks["wrong_password_rejection"] = False
            except AuthenticationError:
                checks["wrong_password_rejection"] = True
            modified = bytearray(binary_container); modified[-1] ^= 1
            try:
                decryption.decrypt_bytes(bytes(modified), password)
                checks["ciphertext_corruption_detection"] = False
            except AuthenticationError:
                checks["ciphertext_corruption_detection"] = True
            mismatch_container = encryption.encrypt_bytes(b"book mismatch", password)
            (temp / "1342.txt").write_bytes(corpus + b"modified")
            try:
                decryption.decrypt_bytes(mismatch_container, password)
                checks["book_mismatch_detection"] = False
            except CorpusError:
                checks["book_mismatch_detection"] = True
    except Exception as exc:
        checks["unhandled_error"] = False
        checks["error_type"] = exc.__class__.__name__
    success = all(value is True for value in checks.values() if isinstance(value, bool))
    report = {"status": "ALL SECURITY COMPONENTS OPERATIONAL" if success else "SECURITY SELF-TEST FAILED", "checks": checks}
    (paths.root / "security_self_test.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return success, report
