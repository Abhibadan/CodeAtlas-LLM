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


class ProjectStatusEnum(str, enum.Enum):
    """Enum for project status - like Mongoose enum"""
    Active = "Active"
    Inactive = "Inactive"
    Archived = "Archived"


class Project(Document):
    """
    Project Schema - Mongoose-like ODM using MongoEngine
    
    Usage:
        # Create
        project = Project(
            title="My Project",
            description="Description",
            status=ProjectStatusEnum.Active
        )
        project.save()
        
        # Query
        projects = Project.objects(status=ProjectStatusEnum.Active)
        project = Project.objects(title="My Project").first()
        
        # Update
        project.title = "Updated Title"
        project.save()
        
        # Delete
        project.delete()
    """
    
    # Reference fields (like Mongoose ref)
    created_by = ObjectIdField()
    members = ListField(ObjectIdField(), default=list)
    
    # String fields
    title = StringField(required=True,max_length=200)
    description = StringField()
    language = StringField(max_length=50)
    
    # Git information
    git_link = StringField()
    git_username = StringField()
    git_password = StringField()  # Consider encrypting this!
    git_branch = StringField(default="main")
    
    # Unique identifier
    uuid = StringField(unique=True, sparse=True)
    scan_version = StringField()
    
    # Status and flags
    is_deleted = BooleanField(default=False)
    status = StringField(choices=[s.value for s in ProjectStatusEnum], default=ProjectStatusEnum.Active.value)
    
    # Timestamps (auto-managed like Mongoose timestamps)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    
    # Meta configuration (like Mongoose schema options)
    meta = {
        'collection': 'projects',  # Collection name
        'strict': False,  # Allow unknown fields like __v from Mongoose
        'indexes': [
            'created_by',
            'status',
            'is_deleted',
            'uuid',
            '-createdAt',  # Descending index
            {
                'fields': ['created_by', 'is_deleted', 'status'],
                'name': 'compound_query_index'
            }
        ],
        'ordering': ['-createdAt']  # Default ordering
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp (like Mongoose pre-save hook)"""
        self.updatedAt = datetime.utcnow()
        return super(Project, self).save(*args, **kwargs)
    
    def soft_delete(self):
        """Soft delete method"""
        self.is_deleted = True
        self.save()
    
    def restore(self):
        """Restore soft-deleted document"""
        self.is_deleted = False
        self.save()
    
    @classmethod
    def find_active(cls):
        """Find all active (non-deleted) projects"""
        return cls.objects(is_deleted=False)
    
    @classmethod
    def find_deleted(cls):
        """Find all deleted projects"""
        return cls.objects(is_deleted=True)
    
    @classmethod
    def find_by_uuid(cls, uuid):
        """Find project by UUID"""
        return cls.objects(uuid=uuid).first()
    
    @classmethod
    def find_by_id(cls, id):
        """Find projects by id"""
        return cls.objects(id=id).first()
    
    @classmethod
    def find(cls,*args,**kwargs):
        """Find projects by args and kwargs"""
        return cls.objects(*args,**kwargs)
    
    @property
    def projectName(self):
        """Backward compatibility: alias for title field"""
        return self.title

    def __str__(self):
        """String representation"""
        return f"Project: {self.title or 'Untitled'} ({self.id})"
