from peewee import Model, IntegerField, DateTimeField, CharField, ForeignKeyField
from playhouse.postgres_ext import JSONField
from datetime import datetime
from enum import Enum
from util.db import DbManager
from user import User
    
class EventStatus(Enum):
    PENDING, ANNOUNCED = range(2)

class Event(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="events", on_delete="CASCADE", null=False)
    date_created = DateTimeField(null=False, default=datetime.now)
    title = CharField()
    status = IntegerField(default=EventStatus.PENDING)
    image_url = CharField(null=True, default="")
    data = JSONField(null=True, default={})

    class Meta:
        database = DbManager().get_db()

    def __str__(self):
        return f"{self.id} - {self.title}"