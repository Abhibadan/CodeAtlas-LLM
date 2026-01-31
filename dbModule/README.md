# MongoEngine (Mongoose-like) Schemas

This is a **Mongoose-like ODM** setup using MongoEngine for Python. It provides the same developer experience as Mongoose in Node.js.

## Available Schemas

- **Project** - Main project schema
- **Markdown** - Markdown files associated with projects
- **Description** - Description files associated with projects

## Installation

```bash
pip install mongoengine
```

## Quick Start

### 1. Connect to Database

```python
from dbModule import init_db

# Connect (like mongoose.connect())
init_db(database_name='my_database', host='mongodb://localhost:27017/')

# Or use environment variables
# MONGO_DB_NAME=my_database
# MONGO_URI=mongodb://localhost:27017/
init_db()
```

### 2. Create a Document

```python
from dbModule import Project, ProjectStatusEnum
from bson import ObjectId

# Create new project (like new Model())
project = Project(
    title="My Project",
    description="A sample project",
    language="Python",
    status=ProjectStatusEnum.Active.value,
    created_by=ObjectId()
)

# Save to database (like .save())
project.save()
print(f"Created: {project.id}")
```

### 3. Query Documents

```python
# Find all (like Model.find())
all_projects = Project.objects()

# Find with filters (like Model.find({ status: 'Active' }))
active_projects = Project.objects(status=ProjectStatusEnum.Active.value)

# Find one (like Model.findOne())
project = Project.objects(title="My Project").first()

# Find by ID (like Model.findById())
project = Project.objects(id=project_id).first()

# Count (like Model.countDocuments())
count = Project.objects(is_deleted=False).count()
```

### 4. Update Documents

```python
# Method 1: Modify and save
project = Project.objects(id=project_id).first()
project.title = "Updated Title"
project.save()  # updatedAt auto-updates

# Method 2: Update directly (like Model.updateOne())
Project.objects(id=project_id).update(
    set__title="Updated Title",
    set__description="New description"
)
```

### 5. Delete Documents

```python
# Soft delete (custom method)
project.soft_delete()

# Restore soft-deleted
project.restore()

# Hard delete (like Model.deleteOne())
project.delete()

# Delete many (like Model.deleteMany())
deleted_count = Project.objects(is_deleted=True).delete()
```

### 6. Advanced Queries

```python
# Multiple conditions
projects = Project.objects(
    status=ProjectStatusEnum.Active.value,
    is_deleted=False,
    language="Python"
)

# Ordering (like .sort())
recent = Project.objects().order_by('-createdAt')  # Descending
oldest = Project.objects().order_by('createdAt')   # Ascending

# Pagination (like .skip().limit())
page_1 = Project.objects().limit(10)
page_2 = Project.objects().skip(10).limit(10)

# Text search
projects = Project.objects(title__icontains="test")

# In query
user_ids = [ObjectId(), ObjectId()]
projects = Project.objects(created_by__in=user_ids)
```

### 7. Custom Methods

```python
# Instance methods
project.add_member(user_id)
project.remove_member(user_id)
project.soft_delete()
project.restore()

# Class methods (like Mongoose statics)
active_projects = Project.find_active()
user_projects = Project.find_by_user(user_id)
member_projects = Project.find_by_member(user_id)
```

## Schema Features

### Auto-managed Timestamps
- `createdAt` - Automatically set on creation
- `updatedAt` - Automatically updated on every save

### Indexes
Automatically created indexes:
- `created_by`
- `status`
- `is_deleted`
- `uuid` (unique)
- `createdAt` (descending)
- Compound index: `(created_by, is_deleted, status)`

### Validation
- Field types are automatically validated
- Unique constraints (e.g., `uuid`)
- String max lengths
- Enum choices (status field)

## Comparison with Mongoose

| Mongoose (Node.js) | MongoEngine (Python) |
|-------------------|---------------------|
| `mongoose.connect()` | `init_db()` |
| `new Model()` | `Model()` |
| `.save()` | `.save()` |
| `Model.find()` | `Model.objects()` |
| `Model.findOne()` | `Model.objects().first()` |
| `Model.findById()` | `Model.objects(id=...).first()` |
| `.updateOne()` | `.objects().update()` |
| `.deleteOne()` | `.delete()` |
| `.countDocuments()` | `.objects().count()` |
| `.sort()` | `.order_by()` |
| `.limit()` | `.limit()` |
| `.skip()` | `.skip()` |

## Environment Variables

```bash
# .env file
MONGO_DB_NAME=codeatlas
MONGO_URI=mongodb://localhost:27017/
```

## Full Example

```python
from dbModule import init_db, Project, ProjectStatusEnum
from bson import ObjectId

# Connect to database
init_db()

# Create project
project = Project(
    title="CodeAtlas",
    description="Code analysis platform",
    language="Python",
    status=ProjectStatusEnum.Active.value,
    created_by=ObjectId()
)
project.save()

# Query
projects = Project.find_active()
for p in projects:
    print(f"{p.title} - {p.status}")

# Update
project.title = "CodeAtlas v2"
project.save()

# Delete
project.soft_delete()
```

## See Also

- Full examples: `examples/project_example.py`
- MongoEngine docs: http://docs.mongoengine.org/
