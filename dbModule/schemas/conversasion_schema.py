from mongoengine import (
    Document, 
    StringField, 
    BooleanField, 
    DateTimeField,
    ObjectIdField,
    ListField,
    ReferenceField
)
from datetime import datetime
import enum


class ConversationTypeEnum(enum.Enum):
    """Enum for conversation type"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"

class ConversationRoleEnum(enum.Enum):
    """Enum for conversation role"""
    USER = "user"
    ASSISTANT = "assistant"



class Conversation(Document):

    chat_id = ObjectIdField()
    user_id = ObjectIdField()
    content = StringField()
    type = StringField(choices=[s.value for s in ConversationTypeEnum], default=ConversationTypeEnum.TEXT.value)
    role = StringField(choices=[s.value for s in ConversationRoleEnum], default=ConversationRoleEnum.USER.value)

    meta = {
        'collection': 'chats',  # Collection name
        'strict': False,  # Allow unknown fields like __v from Mongoose
        'indexes': [
            'chat_id',
            'user_id',
            'type',
            'role',
        ],
        'ordering': ['_id']  # Default ordering
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp (like Mongoose pre-save hook)"""
        self.updatedAt = datetime.utcnow()
        return super(Conversation, self).save(*args, **kwargs)
    
    @classmethod
    def find_by_id(cls, id):
        """Find conversation by id"""
        return cls.objects(id=id).first()
    
    @classmethod
    def find_by_chat_id(cls, chat_id):
        """Find conversation by chat_id"""
        return cls.objects(chat_id=chat_id)
    
    
    @classmethod
    def find(cls,*args,**kwargs):
        """Find conversation by args and kwargs"""
        return cls.objects(*args,**kwargs)
    

    def __str__(self):
        """String representation"""
        return f"Conversation: {self.content} ({self.id})"
