from pathlib import Path


class BookCache:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, gutenberg_id: int) -> Path:
        return self.directory / f"pg{gutenberg_id}.txt"

    def contains(self, gutenberg_id: int) -> bool:
        return self.path_for(gutenberg_id).is_file()

