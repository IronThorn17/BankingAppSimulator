import os
import sqlite3

DB_FILENAME = "banking.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    return sqlite3.connect(DB_FILENAME)


def initialize_database():
    if not os.path.exists(DB_FILENAME):
        print("[INFO] No database found. Creating new one...")
        with open(SCHEMA_PATH, "r") as f:
            schema = f.read()
        conn = sqlite3.connect(DB_FILENAME)
        conn.executescript(schema)
        conn.commit()
        conn.close()
        print("[INFO] Database created and initialized.")
    else:
        print("[INFO] Database found. Using existing one.")