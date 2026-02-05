from mongoengine import Document, StringField, ListField, DateTimeField, ObjectIdField
from datetime import datetime


class Markdown(Document):
    
    projectId = ObjectIdField(required=True)
    filePath = StringField()
    fileName = StringField()
    content = StringField()
    relatedNodeIds = ListField(StringField(), default=list)
    matchType = StringField(default="unmatched")
    scanVersion = StringField()
    
    # Timestamps
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    
    # Meta configuration
    meta = {
        'collection': 'markdowns',
        'strict': False,  # Allow unknown fields like __v from Mongoose
        'indexes': [
            'projectId',
            'scanVersion',
            'filePath',
        ],
        'ordering': ['-createdAt']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp"""
        self.updatedAt = datetime.utcnow()
        return super(Markdown, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"Markdown: {self.fileName or self.filePath or 'Unknown'} ({self.id})"


class Description(Document):
    """
    Description Schema - MongoEngine ODM
    
    Usage:
        # Create
        description = Description(
            projectId=ObjectId(pid),
            filePath="/path/to/file",
            content="Description content"
        )
        description.save()
        
        # Query
        descriptions = Description.objects(projectId=project_id)
        description = Description.objects(filePath="/path/to/file").first()
    """
    
    projectId = ObjectIdField(required=True)
    filePath = StringField()
    fileName = StringField()
    content = StringField()
    relatedNodeIds = ListField(StringField(), default=list)
    matchType = StringField(default="unmatched")
    scanVersion = StringField()
    
    # Timestamps
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    
    # Meta configuration
    meta = {
        'collection': 'descriptions',
        'strict': False,  # Allow unknown fields like __v from Mongoose
        'indexes': [
            'projectId',
            'scanVersion',
            'filePath',
        ],
        'ordering': ['-createdAt']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp"""
        self.updatedAt = datetime.utcnow()
        return super(Description, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"Description: {self.fileName or self.filePath or 'Unknown'} ({self.id})"
