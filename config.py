import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "CHROMA_HOST": os.getenv("CHROMA_HOST"),
    "CHROMA_PORT": os.getenv("CHROMA_PORT"),
    "CHROMA_COLLECTION": os.getenv("CHROMA_COLLECTION"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "lm-studio"),  # LMStudio doesn't need real API key
    "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"),
    "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
    "CHAT_MODEL": os.getenv("CHAT_MODEL", "gpt-3.5-turbo"),
    "NEO4J_URI": os.getenv("NEO4J_URI"),
    "NEO4J_USER": os.getenv("NEO4J_USER"),
    "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
    "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
    "MONGO_URI": os.getenv("MONGO_URI"),
    "MONGO_DB": os.getenv("MONGO_DB"),
    "CHROMA_PERSIST_DIR": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
}