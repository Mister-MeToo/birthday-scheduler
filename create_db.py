import sqlite3

conn = sqlite3.connect('birthdays.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    birthday TEXT NOT NULL,
    message TEXT
)
''')

conn.commit()
conn.close()

print("Database created successfully!")