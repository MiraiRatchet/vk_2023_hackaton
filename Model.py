class Model:
    class Meta:
        table_name = None
        database = None

    @classmethod
    def select(cls):
        if cls.Meta.database is None:
            raise ValueError("Database connection not set")

        cursor = cls.Meta.database.execute(
            f"SELECT * FROM {cls.Meta.table_name}"
        )
        rows = cursor.fetchall()
        instances = []
        for row in rows:
            instance = cls()
            for column, value in zip(cursor.description, row):
                setattr(instance, column[0], value)
            instances.append(instance)

        return instances
