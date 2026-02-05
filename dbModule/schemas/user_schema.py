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

class User(Document):

    full_name = StringField()
    profile_image = StringField()
    email = StringField()
    password = StringField()
    email_verification_otp = StringField()
    status = StringField()
    roles = ListField(ObjectIdField(), default=list)
    active_role = ObjectIdField()
    is_deleted = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'users',  # Collection name
        'strict': False,  # Allow unknown fields like __v from Mongoose
        'indexes': [
            'full_name',
            {
                'fields': ['email'],
                'unique': True,
                'partialFilterExpression': {'is_deleted': False},
                'name': 'email_1'
            },
            'is_deleted',
            'status',
            'active_role',
            'roles',
            'createdAt',
            'updatedAt',
        ],
        'ordering': ['-createdAt']  # Default ordering
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp (like Mongoose pre-save hook)"""
        self.updatedAt = datetime.utcnow()
        return super(User, self).save(*args, **kwargs)
    
    
    @classmethod
    def find_by_id(cls, id):
        """Find conversation by id"""
        return cls.objects(id=id).first()
    
    @classmethod
    def find(cls,*args,**kwargs):
        """Find conversation by args and kwargs"""
        return cls.objects(*args,**kwargs)
    
    @classmethod
    def find_by_role(cls, role):
        """Find conversation by role"""
        return cls.objects(role=role)
    
    

    def __str__(self):
        """String representation"""
        return f"User: {self.full_name} ({self.id})"