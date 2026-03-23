import sqlite3

conn = sqlite3.connect("login.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS login (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL UNIQUE,
    secondName TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()
