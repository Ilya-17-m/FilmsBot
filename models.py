from peewee import SqliteDatabase, Model, CharField, AutoField

db = SqliteDatabase('my_database.db')



class BaseModel(Model):

    class Meta:
        database = db


class User(BaseModel):
    user_id = AutoField(primary_key=True)
    username = CharField(null=False)
    first_name = CharField(null=False)
    last_name = CharField(null=True)


def create_model() -> None:
    db.create_tables([User])
