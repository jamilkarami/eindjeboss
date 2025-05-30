from peewee import Model, IntegerField, DateTimeField, CharField, ForeignKeyField
from enum import Enum
from datetime import datetime

from user import User
from util.db import DbManager

class TicketStatus(Enum):
    OPEN = 1
    IN_PROGRESS = 2
    CLOSED = 3

class Ticket(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="tickets")
    date_created = DateTimeField(null=False, default=datetime.now)
    title = CharField(null=False)
    status = IntegerField(null=False, default=TicketStatus.OPEN)

    class Meta:
        database = DbManager().get_db()

class TicketAuditLog(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="audit_logs", on_delete="CASCADE")
    ticket = ForeignKeyField(Ticket, backref="audit_logs", on_delete="CASCADE")
    action = IntegerField(null=False)
    date_created = DateTimeField(null=False, default=datetime.now)

    class Meta:
        database = DbManager().get_db()

class TicketNote(Model):
    id = IntegerField(primary_key=True)
    author = ForeignKeyField(User, backref="notes")
    ticket = ForeignKeyField(Ticket, backref="notes")
    content = CharField(null=False)
    date_created = DateTimeField(null=False, default=datetime.now)

    class Meta:
        database = DbManager().get_db()

TicketNotes = TicketNote.ticket.get_through_model()
TicketAuditLogs = TicketAuditLog.ticket.get_through_model()