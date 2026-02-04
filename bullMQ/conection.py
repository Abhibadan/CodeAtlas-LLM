"""
BullMQ Redis Connection
Simple Redis connection using configuration from config.py
"""

from config import redis_config


def get_connection_opts() -> dict:
    """
    Get Redis connection options from environment configuration.
    
    Returns:
        Dictionary with connection parameters for BullMQ
    """
    opts = {
        "host": redis_config["host"],
        "port": redis_config["port"],
        "db": redis_config["db"],
    }
    
    if redis_config["password"]:
        opts["password"] = redis_config["password"]
    
    return opts


# Connection options loaded from config
connection_opts = get_connection_opts()
