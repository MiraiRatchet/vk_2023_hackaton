from Database import MyDatabase

class MetaModel(type):
    def __new__(mcs, name, bases, attrs):
        return super().__new__(mcs, name, bases, attrs)

    def __setattr__(cls, name, value):
        return super().__setattr__(name, value)



class Model(metaclass=MetaModel):
    _meta = None

    @classmethod
    def select(cls, *fields):
        query = "SELECT * FROM "
        return query

    @classmethod
    def get(cls, *query, **kwargs):
        query = cls.select().where(*query, **kwargs)
        return query.get()

    @classmethod
    def update(cls, *update, **kwargs):
        query = cls._meta.database.update(*update).table(cls._meta.table_name).where(**kwargs)
        return query.execute()



class Artist(Model):
    class Meta:
        table_name=""