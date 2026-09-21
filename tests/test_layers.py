import os

from core.geographic_layer import transform as geo
from core.nationality_layer import transform as nationality


def test_nationality_forward_reverse(library):
    data, key, nonce = b"layer one", os.urandom(32), os.urandom(32)
    books = library.books(ready_only=True)
    transformed = nationality(data, books, key, nonce, 7)
    assert transformed != data and nationality(transformed, books, key, nonce, 7) == data


def test_geographic_forward_reverse(library):
    data, key, nonce = b"layer two", os.urandom(32), os.urandom(32)
    books = library.books(ready_only=True)
    transformed = geo(data, books, key, nonce, 7)
    assert transformed != data and geo(transformed, books, key, nonce, 7) == data

