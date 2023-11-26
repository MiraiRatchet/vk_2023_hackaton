from Database import MyDatabase
from Model import Model

db = MyDatabase("example.db")


class Artist(Model):
    class Meta:
        database = db
        table_name = "users"


instances = Artist.select()

print(instances)

db.close_connection()