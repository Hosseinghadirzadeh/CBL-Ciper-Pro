from gutenberg.client import GutenbergClient


def download_book(result):
    return GutenbergClient().download(result)

