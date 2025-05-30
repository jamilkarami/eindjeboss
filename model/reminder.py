from peewee import Model, IntegerField, DateTimeField, CharField, BooleanField, ManyToManyField

from user import User
from util.db import DbManager

class Reminder(Model):
    id = IntegerField(primary_key=True)
    reminder_time = DateTimeField()
    guild_id = IntegerField()
    date_created = DateTimeField()
    title = CharField()
    daily = BooleanField(default=False)
    users = ManyToManyField(User, backref="reminders")

    class Meta:
        database = DbManager().get_db()

    def __str__(self):
        return f"{self.id} - {self.title}"
    
UserReminders = Reminder.users.get_through_model()