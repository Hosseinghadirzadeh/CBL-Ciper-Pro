from gutenberg.client import GutenbergClient


def test_parse_gutenberg_search_opds():
    xml = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://www.gutenberg.org/ebooks/1342.opds</id><title>Pride and Prejudice</title><content>Jane Austen</content></entry></feed>'''
    result = GutenbergClient.parse_opds(xml)
    assert [(item.gutenberg_id, item.title, item.author) for item in result] == [(1342, "Pride and Prejudice", "Jane Austen")]


def test_parse_gutenberg_book_opds_and_deduplicate():
    xml = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>urn:gutenberg:1342:2</id><title>Pride and Prejudice</title><author><name>Jane Austen</name></author></entry><entry><id>urn:gutenberg:1342:3</id><title>Pride and Prejudice</title></entry></feed>'''
    result = GutenbergClient.parse_opds(xml)
    assert len(result) == 1
    assert result[0].gutenberg_id == 1342
    assert result[0].author == "Jane Austen"
