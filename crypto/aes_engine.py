from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.errors import AuthenticationError


def encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes) -> bytes:
    return AESGCM(key).encrypt(nonce, plaintext, aad)


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise AuthenticationError("Incorrect password or corrupted file.") from exc

