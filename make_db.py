import sqlite3

conn = sqlite3.connect("example.db")

# conn.execute("""CREATE TABLE users
#              (id INTEGER PRIMARY KEY,
#              name TEXT NOT NULL,
#              age INTEGER NOT NULL);""")

# conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 25)")
# conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 30)")

cursor = conn.execute("SELECT * FROM users")
for row in cursor:
    print(row)

conn.close()