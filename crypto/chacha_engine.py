from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from core.errors import AuthenticationError


def encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes) -> bytes:
    return ChaCha20Poly1305(key).encrypt(nonce, plaintext, aad)


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    try:
        return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise AuthenticationError("Incorrect password or corrupted file.") from exc

