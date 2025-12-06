"""
MongoDB Database Connection Module
Handles all database interactions for the AI system
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import Optional, List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Handles MongoDB connection and operations"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Singleton pattern for database connection"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection"""
        if self._client is None:
            try:
                self._client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
                # Test connection
                self._client.admin.command('ping')
                self._db = self._client[DATABASE_NAME]
                logger.info(f"Successfully connected to MongoDB: {DATABASE_NAME}")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    def get_database(self):
        """Return database instance"""
        return self._db
    
    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        return self._db[collection_name]
    
    def insert_freelancer(self, freelancer_data: Dict[str, Any]) -> str:
        """Insert a freelancer document"""
        collection = self.get_collection(FREELANCERS_COLLECTION)
        result = collection.insert_one(freelancer_data)
        return str(result.inserted_id)
    
    def insert_project(self, project_data: Dict[str, Any]) -> str:
        """Insert a project document"""
        collection = self.get_collection(PROJECTS_COLLECTION)
        result = collection.insert_one(project_data)
        return str(result.inserted_id)
    
    def insert_many_freelancers(self, freelancers: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple freelancer documents"""
        collection = self.get_collection(FREELANCERS_COLLECTION)
        result = collection.insert_many(freelancers)
        return [str(id) for id in result.inserted_ids]
    
    def insert_many_projects(self, projects: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple project documents"""
        collection = self.get_collection(PROJECTS_COLLECTION)
        result = collection.insert_many(projects)
        return [str(id) for id in result.inserted_ids]
    
    def get_all_freelancers(self) -> List[Dict[str, Any]]:
        """Retrieve all freelancers"""
        collection = self.get_collection(FREELANCERS_COLLECTION)
        return list(collection.find({}))
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Retrieve all projects"""
        collection = self.get_collection(PROJECTS_COLLECTION)
        return list(collection.find({}))
    
    def count_freelancers(self) -> int:
        """Count total freelancers"""
        collection = self.get_collection(FREELANCERS_COLLECTION)
        return collection.count_documents({})
    
    def count_projects(self) -> int:
        """Count total projects"""
        collection = self.get_collection(PROJECTS_COLLECTION)
        return collection.count_documents({})
    
    def clear_collection(self, collection_name: str):
        """Clear all documents from a collection"""
        collection = self.get_collection(collection_name)
        result = collection.delete_many({})
        logger.info(f"Cleared {result.deleted_count} documents from {collection_name}")
        return result.deleted_count
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            logger.info("Database connection closed")


# Convenience function for getting database instance
def get_db_connection() -> DatabaseConnection:
    """Get database connection instance"""
    return DatabaseConnection()


if __name__ == "__main__":
    # Test database connection
    try:
        db = get_db_connection()
        print(f"✓ Database connected successfully")
        print(f"✓ Database name: {DATABASE_NAME}")
        print(f"✓ Freelancers count: {db.count_freelancers()}")
        print(f"✓ Projects count: {db.count_projects()}")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
