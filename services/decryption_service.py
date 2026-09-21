from __future__ import annotations

import base64
from pathlib import Path

from core.container_format import unpack
from core.cbl_geo_cipher import CBLGeoCipher
from core.token_codec import parse_json
from crypto.aes_engine import decrypt as aes_decrypt
from crypto.hkdf_engine import separate_keys
from crypto.password_kdf import derive_root_key
from database.db import Database


class DecryptionService:
    def __init__(self, db: Database):
        self.cipher = CBLGeoCipher(db)

    def decrypt_bytes(self, blob: bytes, password: str, progress=None) -> tuple[bytes, dict]:
        header, ciphertext, aad = unpack(blob)
        try:
            salt = base64.b64decode(header["salt"], validate=True)
            nonce = base64.b64decode(header["aes_nonce"], validate=True)
            message_nonce = base64.b64decode(header["message_nonce"], validate=True)
        except Exception as exc:
            from core.errors import ContainerError
            raise ContainerError("Corrupted LBCX header") from exc
        keys = separate_keys(derive_root_key(password, salt, header["argon2"]))
        payload = parse_json(aes_decrypt(keys["aes"], nonce, ciphertext, aad))
        return self.cipher.decode(payload, keys, message_nonce, progress=progress), payload

    def decrypt_file(self, source: str | Path, target: str | Path, password: str, progress=None) -> None:
        data, _ = self.decrypt_bytes(Path(source).read_bytes(), password, progress=progress)
        target = Path(target)
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.write_bytes(data)
        temporary.replace(target)
