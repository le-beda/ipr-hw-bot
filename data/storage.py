import sqlite3

conn = sqlite3.connect("/ipr-bot/db/banned.db", check_same_thread=False)

cursor = conn.cursor()
