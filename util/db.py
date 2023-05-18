import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from pymongo.server_api import ServerApi

load_dotenv()
url = os.getenv('MONGO_DB_URL')
pw = os.getenv('MONGO_DB_PASSWORD')
db_name = os.getenv('MONGO_DB_NAME')


class DbManager():
    def __init__(self):
        uri = url % pw
        self.dbclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
        self.db = self.dbclient[db_name]

    def get_collection(self, collection_name) -> Collection:
        return self.db[collection_name]
