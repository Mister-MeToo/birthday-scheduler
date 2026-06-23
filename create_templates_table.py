# create_templates_table.py

import sqlite3

conn = sqlite3.connect("birthdays.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    message TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ Templates table created")