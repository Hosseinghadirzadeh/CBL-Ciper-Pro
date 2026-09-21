import secrets


def random_bytes(length: int) -> bytes:
    return secrets.token_bytes(length)

