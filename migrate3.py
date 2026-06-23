import sqlite3

conn = sqlite3.connect('birthdays.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        birthday_id INTEGER NOT NULL,
        sent_date TEXT NOT NULL
    )
""")

conn.commit()
conn.close()
print("Done!")