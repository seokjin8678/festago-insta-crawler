import datetime

from peewee import *

database = SqliteDatabase('local_database.db')


class BaseModel(Model):
  class Meta:
    database = database
    legacy_table_names = False


class InstagramAccount(BaseModel):
  id = CharField(primary_key=True)
  name = CharField(null=True)


class InstagramReadHistory(BaseModel):
  id = AutoField(primary_key=True)
  post_id = CharField()
  account_id = ForeignKeyField(InstagramAccount, backref='histories')
  is_festival = BooleanField(null=True)
  posted_at = DateTimeField()
  created_at = DateTimeField(default=datetime.datetime.now)

InstagramReadHistory.add_index(InstagramReadHistory.post_id)
InstagramReadHistory.add_index(InstagramReadHistory.posted_at.desc())