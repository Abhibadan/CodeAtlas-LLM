import os
from dotenv import load_dotenv

load_dotenv()

# ChromaDB Configuration
chroma_config = {
    "host": os.getenv("CHROMA_HOST"),
    "host": os.getenv("CHROMA_PORT"),
    "collection": os.getenv("CHROMA_COLLECTION"),
}

# Google AI Configuration
google_config = {
    "api_key": os.getenv("GOOGLE_API_KEY"),
    "embedding_model": os.getenv("EMBEDDING_MODEL"),
    "chat_model": os.getenv("CHAT_MODEL"),
}

# Neo4j Configuration
neo4j_config = {
    "uri": os.getenv("NEO4J_URI"),
    "user": os.getenv("NEO4J_USER"),
    "password": os.getenv("NEO4J_PASSWORD"),
    "database": os.getenv("NEO4J_DATABASE"),
}

# MongoDB Configuration
mongo_config = {
    "uri": os.getenv("MONGO_URI"),
    "db": os.getenv("MONGO_DB"),
}

# Redis Configuration (for BullMQ)
redis_config = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD"),
}
