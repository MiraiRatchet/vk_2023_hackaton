import sqlite3

DB_NAME = "example.db"


def create_table_orm(cls):
    cls.objects.create_table()
    return cls


class BaseType:
    field_type: str


class IntegerField(BaseType):
    field_type = "INTEGER"


class TextField(BaseType):
    field_type = "TEXT"


class DescriptorObjects:
    def __get__(self, instance, owner):
        return BaseModel(owner)


class BaseModel:
    def __init__(self, model_class):
        self.model_class = model_class

    def create_table(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        table_name = self.model_class.__name__
        custom_fields = []
        for key, value in self.model_class.__dict__.items():
            if not key.startswith("__"):
                field_name = key
                field_type = value.field_type
                field_pair = [field_name, field_type]
                custom_fields.append(" ".join(field_pair))

        query = (
            "CREATE TABLE IF NOT EXISTS"
            f" {table_name} ({', '.join(custom_fields)})"
        )
        cursor.execute(query)
        connection.commit()
        connection.close()

    def select(self, *fields_names):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        table_name = self.model_class.__name__
        fields_names = ", ".join(fields_names)

        query = f"SELECT {fields_names} FROM {table_name}"
        cursor.execute(query)
        result = cursor.fetchall()
        connection.close()
        return result

    def insert_sql(self, obj):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        table_name = self.model_class.__name__
        fields_names = ", ".join(obj.__dict__.keys())

        values_str = ", ".join(["?"] * len(obj.__dict__))

        query = (
            f"INSERT INTO {table_name} ({fields_names}) VALUES ({values_str})"
        )
        values = tuple(obj.__dict__.values())
        cursor.execute(query, values)
        connection.commit()
        connection.close()

    def delete(self, **kwargs):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        table_name = self.model_class.__name__
        value_pairs = [(key, value) for key, value in kwargs.items()]

        where_clauses = " AND ".join(
            f"{key} = ?" for key, value in value_pairs
        )
        query = f"DELETE FROM {table_name} WHERE {where_clauses};"
        values = tuple(value for key, value in value_pairs)
        cursor.execute(query, values)
        connection.commit()
        connection.close()


class Model(BaseModel):
    objects = DescriptorObjects()

    def __init__(self, *args, **kwargs):
        fields = [
            field
            for field in self.__class__.__dict__
            if not field.startswith("__")
        ]

        for i, value in enumerate(args):
            setattr(self, fields[i], value)

        for field, value in kwargs.items():
            setattr(self, field, value)

    def __str__(self):
        attrs_format = ", ".join(
            [f"{field}={value}" for field, value in self.__dict__.items()]
        )
        return f"{self.__class__.__name__}: ({attrs_format})"

