import os
from typing import Optional

from dotenv import load_dotenv
from peewee import PostgresqlDatabase

load_dotenv()

db_name: Optional[str] = os.getenv('POSTGRES_DB')
db_user: Optional[str] = os.getenv('POSTGRES_USER')
db_password: Optional[str] = os.getenv('POSTGRES_PASSWORD')
db_host: Optional[str] = os.getenv('POSTGRES_HOST')
db_port: Optional[int] = int(os.getenv('POSTGRES_PORT') or 5432)

if not all([db_name, db_user, db_password, db_host, db_port]):
    raise ValueError("Missing required Postgres environment variables")

class DbManager:
    def __init__(self):
        self.db: PostgresqlDatabase = PostgresqlDatabase(db_name, user=db_user, password=db_password, host=db_host, port=db_port, autoconnect=False)

    def get_db(self):
        return self.db
