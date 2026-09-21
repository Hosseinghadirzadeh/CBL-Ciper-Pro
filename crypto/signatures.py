from __future__ import annotations

import base64
import json
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypto.password_kdf import DEFAULT_PARAMS, derive_root_key


def generate_keypair(password: str) -> tuple[bytes, bytes]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    raw_private = private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    salt, nonce = os.urandom(16), os.urandom(12)
    key = derive_root_key(password, salt)
    encrypted = AESGCM(key).encrypt(nonce, raw_private, b"LBC-ED25519-v1")
    envelope = {"v": 1, "salt": base64.b64encode(salt).decode(), "nonce": base64.b64encode(nonce).decode(), "argon2": DEFAULT_PARAMS, "data": base64.b64encode(encrypted).decode()}
    return json.dumps(envelope, sort_keys=True).encode(), public


def _load_private(envelope: bytes, password: str) -> Ed25519PrivateKey:
    obj = json.loads(envelope)
    salt, nonce, data = (base64.b64decode(obj[k]) for k in ("salt", "nonce", "data"))
    raw = AESGCM(derive_root_key(password, salt, obj["argon2"])).decrypt(nonce, data, b"LBC-ED25519-v1")
    return Ed25519PrivateKey.from_private_bytes(raw)


def sign(data: bytes, encrypted_private_key: bytes, password: str) -> bytes:
    return _load_private(encrypted_private_key, password).sign(data)


def verify(data: bytes, signature: bytes, public_key: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, data)
        return True
    except Exception:
        return False

