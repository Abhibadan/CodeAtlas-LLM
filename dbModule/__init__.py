"""
Database Module - MongoEngine ODM (Mongoose-like)
"""

from .connection import init_db, MongoDBConnection
from .schemas import Project, ProjectStatusEnum, Markdown, Description, Conversation, ConversationTypeEnum, ConversationRoleEnum, User

__all__ = [
    "init_db",
    "MongoDBConnection",
    "Project",
    "ProjectStatusEnum",
    "Markdown",
    "Description",
    "Conversation",
    "ConversationTypeEnum",
    "ConversationRoleEnum",
    "User"
]
