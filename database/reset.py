import os

DB_FILENAME = "banking.db"

if os.path.exists(DB_FILENAME):
    os.remove(DB_FILENAME)
    print("[DEBUG] Database deleted.")
else:
    print("[DEBUG] No database to delete.")