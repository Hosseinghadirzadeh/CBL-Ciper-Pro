"""Curated public-domain starter corpus for automatic online provisioning.

Only books are downloaded from Project Gutenberg. Supplemental author fields are
explicit curated metadata; they are never inferred from book language.
"""

STARTER_CORPUS = [
    {"gutenberg_id": 1342, "title": "Pride and Prejudice", "language": "en", "author": "Jane Austen", "nationality": "British", "birth_country": "England", "birth_city": "Steventon", "latitude": 51.1656, "longitude": -1.2158},
    {"gutenberg_id": 1661, "title": "The Adventures of Sherlock Holmes", "language": "en", "author": "Arthur Conan Doyle", "nationality": "British", "birth_country": "Scotland", "birth_city": "Edinburgh", "latitude": 55.9533, "longitude": -3.1883},
    {"gutenberg_id": 2701, "title": "Moby-Dick", "language": "en", "author": "Herman Melville", "nationality": "American", "birth_country": "United States", "birth_city": "New York City", "latitude": 40.7128, "longitude": -74.0060},
    {"gutenberg_id": 84, "title": "Frankenstein", "language": "en", "author": "Mary Shelley", "nationality": "British", "birth_country": "England", "birth_city": "London", "latitude": 51.5074, "longitude": -0.1278},
    {"gutenberg_id": 11, "title": "Alice's Adventures in Wonderland", "language": "en", "author": "Lewis Carroll", "nationality": "British", "birth_country": "England", "birth_city": "Daresbury", "latitude": 53.3418, "longitude": -2.6350},
    {"gutenberg_id": 345, "title": "Dracula", "language": "en", "author": "Bram Stoker", "nationality": "Irish", "birth_country": "Ireland", "birth_city": "Clontarf", "latitude": 53.3647, "longitude": -6.2068},
    {"gutenberg_id": 98, "title": "A Tale of Two Cities", "language": "en", "author": "Charles Dickens", "nationality": "British", "birth_country": "England", "birth_city": "Portsmouth", "latitude": 50.8198, "longitude": -1.0880},
    {"gutenberg_id": 74, "title": "The Adventures of Tom Sawyer", "language": "en", "author": "Mark Twain", "nationality": "American", "birth_country": "United States", "birth_city": "Florida, Missouri", "latitude": 39.4917, "longitude": -91.7902},
]
