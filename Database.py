import sqlite3


class MyDatabase:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name, fields):
        # Подготавливаем SQL запрос для создания таблицы на основе переданных полей
        sql_query = f"CREATE TABLE {table_name} ({', '.join(fields)})"
        self.cursor.execute(sql_query)
        self.connection.execute(
            "INSERT INTO users (name, age) VALUES ('Alice', 25)"
        )
        self.connection.execute(
            "INSERT INTO users (name, age) VALUES ('Bob', 30)"
        )
        self.connection.commit()

    def execute(self, query):
        return self.connection.execute(query)

    def close_connection(self):
        self.connection.close()
