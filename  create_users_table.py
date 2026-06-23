# create_users_table.py

import sqlite3

conn = sqlite3.connect("birthdays.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    verified INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

print("✅ Users table created")