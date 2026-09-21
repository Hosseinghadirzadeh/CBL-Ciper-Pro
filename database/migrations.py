from database.db import Database


def migrate(path):
    return Database(path)

