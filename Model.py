class Model:
    _meta = None

    @classmethod
    def select(cls, *fields):
        query = cls._meta.database.select(*fields).from_(cls._meta.table_name)
        return query

    @classmethod
    def get(cls, *query, **kwargs):
        query = cls.select().where(*query, **kwargs)
        return query.get()

    @classmethod
    def update(cls, *update, **kwargs):
        query = cls._meta.database.update(*update).table(cls._meta.table_name).where(**kwargs)
        return query.execute()