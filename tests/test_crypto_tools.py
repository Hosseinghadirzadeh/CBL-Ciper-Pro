from crypto.hashing import hash_bytes
from crypto.signatures import generate_keypair, sign, verify


def test_hash_functions():
    assert hash_bytes(b"abc", "SHA-256") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert len(hash_bytes(b"abc", "BLAKE3")) == 64


def test_ed25519_signature():
    private, public = generate_keypair("long password")
    signature = sign(b"message", private, "long password")
    assert verify(b"message", signature, public)
    assert not verify(b"changed", signature, public)

