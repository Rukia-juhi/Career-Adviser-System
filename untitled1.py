# check_schema.py
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "data.sqlite")
print("DB:", DB)
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("PRAGMA table_info(users);")
print("users table columns:")
for row in cur.fetchall():
    print(row)
cur.close()
con.close()
