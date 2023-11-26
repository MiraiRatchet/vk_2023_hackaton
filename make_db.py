from Database import MyDatabase

db = MyDatabase("example.db")
fields = ["id INTEGER PRIMARY KEY", "name TEXT", "age INTEGER"]
db.create_table("users", fields)
db.close_connection()
