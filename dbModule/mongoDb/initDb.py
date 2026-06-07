"""
MongoDB Connection Setup with MongoEngine
"""

from mongoengine import connect, disconnect
import os


class MongoDBConnection:
    """MongoDB connection manager - Singleton pattern"""
    
    _instance = None
    _connected = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def connect_db(cls, database_name: str = None, host: str = None, **kwargs):
        """
        Connect to MongoDB
        
        Args:
            database_name: Database name
            host: MongoDB connection string
            **kwargs: Additional connection parameters
            
        Example:
            MongoDBConnection.connect_db(
                database_name='my_database',
                host='mongodb://localhost:27017/'
            )
            
            # Or with environment variables:
            MongoDBConnection.connect_db()
        """
        if cls._connected:
            print("Already connected to MongoDB")
            return
        
        # Default values from environment or fallback
        db_name = database_name or os.getenv('MONGO_DB_NAME', 'codeatlas')
        db_host = host or os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        
        try:
            connect(
                db=db_name,
                host=db_host,
                **kwargs
            )
            cls._connected = True
            print(f"✓ Connected to MongoDB: {db_name}")
        except Exception as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    def disconnect_db(cls):
        """Disconnect from MongoDB"""
        if cls._connected:
            disconnect()
            cls._connected = False
            print("✓ Disconnected from MongoDB")
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if connected to MongoDB"""
        return cls._connected


# Convenience function
def init_db(database_name: str = None, host: str = None):
    """
    Initialize MongoDB connection
    
    """
    MongoDBConnection.connect_db(database_name, host)
