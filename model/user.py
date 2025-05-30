from peewee import Model, IntegerField, DateField, DateTimeField, CharField, ForeignKeyField
from playhouse.postgres_ext import JSONField
from datetime import datetime
from enum import Enum

from util.db import DbManager

db = DbManager().get_db()

class AuditLogAction(Enum):
    USER_MUTED = "user_muted"
    USER_UNMUTED = "user_unmuted"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    USER_KICKED = "user_kicked"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"

class User(Model):
    id = IntegerField(primary_key=True)
    dob = DateField()
    username = CharField()
    pronouns = CharField()
    date_joined = DateTimeField()

    class Meta:
        database = db

    def __str__(self):
        return f"{self.id} - {self.username}"

class UserAuditLog(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="audit_logs", on_delete="CASCADE", null=False)
    action = IntegerField(null=False)
    date_created = DateTimeField(null=False, default=datetime.now)
    note = CharField(null=True, default="")

    class Meta:
        database = db

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.action} - {self.date_created}"
    
class UserSettings(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="settings", on_delete="CASCADE", null=False)
    settings = JSONField(null=True, default={})

    class Meta:
        database = db

    def __str__(self):
        return f"{self.id} - {self.user.username}"