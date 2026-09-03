import sqlite3
conn = sqlite3.connect('data/revflow.db')
cursor = conn.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="events"')
result = cursor.fetchone()
print(result[0])
conn.close()