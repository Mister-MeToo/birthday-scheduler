import sqlite3

conn = sqlite3.connect('birthdays.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE birthdays ADD COLUMN email TEXT DEFAULT ''")
    print("Email column added!")
except:
    print("Email column already exists")

conn.commit()
conn.close()