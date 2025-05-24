import os
from typing import Optional

from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.server_api import ServerApi

load_dotenv()
url: Optional[str] = os.getenv("MONGO_DB_URL")
pw: Optional[str] = os.getenv("MONGO_DB_PASSWORD")
db_name: Optional[str] = os.getenv("MONGO_DB_NAME")

if not all([url, pw, db_name]):
    raise ValueError("Missing required MongoDB environment variables")


class DbManager:
    def __init__(self):
        uri = url % pw  # type: ignore
        self.dbclient: AsyncMongoClient = AsyncMongoClient(
            uri, server_api=ServerApi("1")
        )
        self.db: Database = self.dbclient[db_name]  # type: ignore

    def get_collection(self, collection_name: str) -> Collection:
        return self.db[collection_name]
