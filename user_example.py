from Database import MyDatabase
from Model import Model


db = MyDatabase("example.db")


class Artist(Model):
    database = db
