from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .config import settings
from .logging import logger as log


class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.files_collection = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(settings.MONGO_URL)
            self.db = self.client[settings.DATABASE_NAME]
            self.files_collection = self.db[settings.COLLECTION_NAME]
            # Test connection
            self.client.admin.command('ping')
            log.info(f"Connected to MongoDB at {settings.MONGO_URL}")
        except ConnectionFailure as e:
            log.error(f"Failed to connect to MongoDB at {settings.MONGO_URL}: {e}")
            self.client = None
            self.db = None
            self.files_collection = None
    
    def get_files_collection(self):
        """Get the files collection"""
        return self.files_collection
    
    def is_connected(self):
        """Check if database is connected"""
        return self.files_collection is not None


# Global database instance
database = Database()
