import sqlite3


class MyDatabase:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name, fields):
        # Подготавливаем SQL запрос для создания таблицы на основе переданных полей
        sql_query = f"CREATE TABLE {table_name} ({', '.join(fields)})"
        self.cursor.execute(sql_query)
        self.connection.commit()

    def close_connection(self):
        self.connection.close()

# Пример использования класса для создания таблицы
db = MyDatabase('example.db')
fields = ["id INTEGER PRIMARY KEY", "name TEXT", "age INTEGER"]
db.create_table('users', fields)
db.close_connection()