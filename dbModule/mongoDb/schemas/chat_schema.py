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


class Chat(Document):

    project_id = ObjectIdField()
    title = StringField()
    user_id = ObjectIdField()
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'chats',  # Collection name
        'strict': False, 
        'indexes': [
            'project_id',
            'user_id',
        ],
        'ordering': ['-createdAt']  # Default ordering
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp"""
        self.updatedAt = datetime.utcnow()
        return super(Chat, self).save(*args, **kwargs)
    
    
    @classmethod
    def find_by_project_id(cls, project_id):
        """Find conversation by project_id"""
        return cls.objects(project_id=project_id)
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """Find conversation by user_id"""
        return cls.objects(user_id=user_id)

    @classmethod
    def find_by_id(cls, id):
        """Find conversation by id"""
        return cls.objects(id=id).first()
    
    @classmethod
    def find(cls,*args,**kwargs):
        """Find conversation by args and kwargs"""
        return cls.objects(*args,**kwargs)
    

    def __str__(self):
        """String representation"""
        return f"Chat: {self.title} ({self.id})"