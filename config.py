import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "CHROMA_HOST": os.getenv("CHROMA_HOST"),
    "CHROMA_PORT": os.getenv("CHROMA_PORT"),
    "CHROMA_COLLECTION": os.getenv("CHROMA_COLLECTION"),
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL"),
    "CHAT_MODEL": os.getenv("CHAT_MODEL"),
    "NEO4J_URI": os.getenv("NEO4J_URI"),
    "NEO4J_USER": os.getenv("NEO4J_USER"),
    "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
    "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
}