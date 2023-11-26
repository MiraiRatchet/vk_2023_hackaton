from orm import *


@create_table_orm
class Person(Model):
    id = IntegerField()
    first_name = TextField()
    last_name = TextField()
    age = IntegerField()


Person.objects.insert_sql(Person(1, "Michael", "Jackson", 30))
Person.objects.insert_sql(Person(2, "Sonic", "Hedgehog", 10))
print(Person.objects.select("last_name", "first_name"))
Person.objects.delete(first_name="Michael")
print(Person.objects.select("last_name", "first_name"))
