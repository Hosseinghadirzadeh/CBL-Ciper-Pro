import hashlib

import pytest

from core.errors import AuthenticationError, CorpusError
from core.container_format import pack, unpack
from services.decryption_service import DecryptionService
from services.encryption_service import EncryptionService


@pytest.mark.parametrize("value", ["Hello World!", "سلام، حالت چطوره؟", "مرحبا بالعالم", "你好，世界", "Hello 🌍 🔐", "a b\tc\nD!", ""])
def test_unicode_roundtrips(library, value):
    encrypted = EncryptionService(library).encrypt_bytes(value.encode(), "correct horse battery staple", text=True)
    recovered, payload = DecryptionService(library).decrypt_bytes(encrypted, "correct horse battery staple")
    assert recovered.decode() == value
    assert payload["kind"] == "text"


def test_binary_roundtrip(library):
    original = bytes(range(256)) + b"\x00\xffbinary"
    encrypted = EncryptionService(library).encrypt_bytes(original, "password")
    recovered, _ = DecryptionService(library).decrypt_bytes(encrypted, "password")
    assert hashlib.sha256(recovered).digest() == hashlib.sha256(original).digest()


def test_container_uses_cbl_geo_name(library):
    encrypted = EncryptionService(library).encrypt_bytes(b"renamed algorithm", "password")
    header, _, _ = unpack(encrypted)
    assert header["cbl_geo_version"] == 1
    assert "lbc_geo_version" not in header


def test_legacy_algorithm_header_is_still_accepted():
    header, ciphertext, _ = unpack(pack({"lbc_geo_version": 1}, b"legacy"))
    assert header["lbc_geo_version"] == 1
    assert ciphertext == b"legacy"


def test_wrong_password(library):
    encrypted = EncryptionService(library).encrypt_bytes(b"secret", "right")
    with pytest.raises(AuthenticationError):
        DecryptionService(library).decrypt_bytes(encrypted, "wrong")


def test_modified_ciphertext(library):
    encrypted = bytearray(EncryptionService(library).encrypt_bytes(b"secret", "right"))
    encrypted[-1] ^= 1
    with pytest.raises(AuthenticationError):
        DecryptionService(library).decrypt_bytes(bytes(encrypted), "right")


def test_wrong_book_hash(library):
    encrypted = EncryptionService(library).encrypt_bytes(b"secret", "right")
    path = next(iter(library.books())).local_path
    with open(path, "ab") as handle:
        handle.write(b"modified")
    with pytest.raises(CorpusError):
        DecryptionService(library).decrypt_bytes(encrypted, "right")


def test_multi_book_references(library):
    encrypted = EncryptionService(library).encrypt_bytes(b"abc", "right")
    _, payload = DecryptionService(library).decrypt_bytes(encrypted, "right")
    assert all(len(token["g"]) == 3 and len(set(token["g"])) == 3 for token in payload["tokens"])
