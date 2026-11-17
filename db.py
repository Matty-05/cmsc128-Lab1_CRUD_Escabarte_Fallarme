import sqlite3

from pathlib import Path

from flask import g


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "todo.db"
SCHEMA = BASE_DIR / "database" / "schema.sql"

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(exception=None):
    connection = g.pop("db", None)

    if connection is not None:
        connection.close()
