from __future__ import annotations

import base64
import os
from pathlib import Path

from app.constants import LBC_GEO_VERSION
from core.container_format import aad_for_header, pack
from core.lbc_geo_cipher import LBCGeoCipher
from core.token_codec import canonical_json
from crypto.aes_engine import encrypt as aes_encrypt
from crypto.hkdf_engine import separate_keys
from crypto.password_kdf import DEFAULT_PARAMS, derive_root_key
from database.db import Database


class EncryptionService:
    def __init__(self, db: Database):
        self.cipher = LBCGeoCipher(db)

    def encrypt_bytes(self, data: bytes, password: str, *, text: bool = False, books_per_symbol: int = 3, original_name: str | None = None, progress=None) -> bytes:
        salt, aes_nonce, message_nonce = os.urandom(16), os.urandom(12), os.urandom(32)
        keys = separate_keys(derive_root_key(password, salt))
        payload = self.cipher.encode(data, keys, message_nonce, books_per_symbol, text=text, progress=progress)
        payload["original_name"] = original_name
        plaintext = canonical_json(payload)
        header = {
            "cipher": "AES-256-GCM", "kdf": "Argon2id", "argon2": DEFAULT_PARAMS,
            "salt": base64.b64encode(salt).decode(), "aes_nonce": base64.b64encode(aes_nonce).decode(),
            "message_nonce": base64.b64encode(message_nonce).decode(), "lbc_geo_version": LBC_GEO_VERSION,
        }
        aad = aad_for_header(header, len(plaintext) + 16)
        ciphertext = aes_encrypt(keys["aes"], aes_nonce, plaintext, aad)
        return pack(header, ciphertext)

    def encrypt_file(self, source: str | Path, target: str | Path, password: str, books_per_symbol: int = 3, progress=None) -> None:
        source = Path(source)
        blob = self.encrypt_bytes(source.read_bytes(), password, books_per_symbol=books_per_symbol, original_name=source.name, progress=progress)
        target = Path(target)
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.write_bytes(blob)
        temporary.replace(target)

