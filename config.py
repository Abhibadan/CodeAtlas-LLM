import os
from dotenv import load_dotenv

load_dotenv()

# ChromaDB Configuration
chroma_config = {
    "host": os.getenv("CHROMA_HOST"),
    "port": os.getenv("CHROMA_PORT"),
    "collection": os.getenv("CHROMA_COLLECTION"),
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

# Kafka Configuration
kafka_config = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(","),
    "group_id": os.getenv("KAFKA_GROUP_ID", "codeatlas-llm-group"),
}

# AI Provider Configuration
ai_config = {
    "provider": os.getenv("AI_PROVIDER", "gemini").lower(),
}

# Google AI Configuration
google_config = {
    "api_key": os.getenv("GOOGLE_API_KEY"),
    "embedding_model": os.getenv("EMBEDDING_MODEL"),
    "chat_model": os.getenv("CHAT_MODEL"),
}

# OpenAI Configuration
openai_config = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    "chat_model": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
}

# Ollama Configuration
ollama_config = {
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "embedding_model": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
    "chat_model": os.getenv("OLLAMA_CHAT_MODEL", "llama3.2"),
}

