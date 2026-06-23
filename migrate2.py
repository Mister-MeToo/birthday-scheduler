import sqlite3

conn = sqlite3.connect('birthdays.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        message TEXT NOT NULL
    )
""")

# Add some default templates
cursor.execute("INSERT INTO templates (name, message) VALUES (?, ?)",
    ("Classic", "Happy Birthday {name}! 🎂 Wishing you a wonderful day!"))
cursor.execute("INSERT INTO templates (name, message) VALUES (?, ?)",
    ("Short & Sweet", "Happy Birthday {name}! 🎉"))
cursor.execute("INSERT INTO templates (name, message) VALUES (?, ?)",
    ("Formal", "Dear {name}, wishing you a very Happy Birthday and a year full of joy and success!"))

conn.commit()
conn.close()
print("Done!")