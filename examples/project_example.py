"""
Example usage of MongoEngine Project schema (Mongoose-like)
"""

from mongoengine import connect
from dbModule.schemas import Project, ProjectStatusEnum
from bson import ObjectId


def main():
    """Demonstrate Mongoose-like usage with MongoEngine"""
    
    # Connect to MongoDB (like mongoose.connect())
    connect('your_database_name', host='mongodb://localhost:27017/')
    
    print("=== MongoEngine (Mongoose-like) Examples ===\n")
    
    # Example 1: Create and Save (like Mongoose)
    print("1. Creating a new project...")
    project = Project(
        created_by=ObjectId(),
        members=[ObjectId(), ObjectId()],
        title="My Awesome Project",
        description="This is a test project",
        language="Python",
        git_link="https://github.com/user/repo",
        git_username="gituser",
        git_password="gitpass",
        git_branch="main",
        uuid="unique-project-uuid-123",
        scan_version="1.0.0",
        status=ProjectStatusEnum.Active.value
    )
    project.save()  # Like Mongoose .save()
    print(f"✓ Created: {project}\n")
    
    # Example 2: Find by ID (like Mongoose .findById())
    print("2. Finding project by ID...")
    found_project = Project.objects(id=project.id).first()
    print(f"✓ Found: {found_project}\n")
    
    # Example 3: Find with filters (like Mongoose .find())
    print("3. Finding active projects...")
    active_projects = Project.objects(status=ProjectStatusEnum.Active.value)
    print(f"✓ Found {active_projects.count()} active project(s)\n")
    
    # Example 4: Find one (like Mongoose .findOne())
    print("4. Finding project by title...")
    project_by_title = Project.objects(title="My Awesome Project").first()
    print(f"✓ Found: {project_by_title}\n")
    
    # Example 5: Update (like Mongoose update)
    print("5. Updating project...")
    project.title = "Updated Project Title"
    project.description = "Updated description"
    project.save()  # updatedAt is auto-updated
    print(f"✓ Updated: {project.title}\n")
    
    # Example 6: Update with .update() (like Mongoose .updateOne())
    print("6. Using update method...")
    Project.objects(id=project.id).update(set__language="JavaScript")
    updated = Project.objects(id=project.id).first()
    print(f"✓ Updated language to: {updated.language}\n")
    
    # Example 7: Add member (custom method)
    print("7. Adding a member...")
    new_member = ObjectId()
    project.add_member(new_member)
    print(f"✓ Added member. Total members: {len(project.members)}\n")
    
    # Example 8: Remove member (custom method)
    print("8. Removing a member...")
    project.remove_member(new_member)
    print(f"✓ Removed member. Total members: {len(project.members)}\n")
    
    # Example 9: Class methods (like Mongoose statics)
    print("9. Using class method to find by user...")
    user_id = project.created_by
    user_projects = Project.find_by_user(user_id)
    print(f"✓ User has {user_projects.count()} project(s)\n")
    
    # Example 10: Find active projects (custom class method)
    print("10. Finding all active projects...")
    active = Project.find_active()
    print(f"✓ Found {active.count()} active project(s)\n")
    
    # Example 11: Soft delete (custom method)
    print("11. Soft deleting project...")
    project.soft_delete()
    print(f"✓ Soft deleted: {project.is_deleted}\n")
    
    # Example 12: Restore (custom method)
    print("12. Restoring project...")
    project.restore()
    print(f"✓ Restored: {not project.is_deleted}\n")
    
    # Example 13: Query with multiple conditions (like Mongoose)
    print("13. Complex query...")
    results = Project.objects(
        status=ProjectStatusEnum.Active.value,
        is_deleted=False,
        language="JavaScript"
    )
    print(f"✓ Found {results.count()} matching project(s)\n")
    
    # Example 14: Ordering (like Mongoose .sort())
    print("14. Getting projects ordered by creation date...")
    recent_projects = Project.objects().order_by('-createdAt').limit(10)
    print(f"✓ Retrieved {recent_projects.count()} recent project(s)\n")
    
    # Example 15: Count (like Mongoose .countDocuments())
    print("15. Counting projects...")
    total = Project.objects().count()
    active_count = Project.objects(is_deleted=False).count()
    print(f"✓ Total: {total}, Active: {active_count}\n")
    
    # Example 16: Delete (like Mongoose .deleteOne())
    print("16. Deleting project...")
    project.delete()
    print("✓ Project deleted permanently\n")
    
    # Example 17: Bulk operations (like Mongoose .insertMany())
    print("17. Creating multiple projects...")
    projects = [
        Project(title=f"Project {i}", status=ProjectStatusEnum.Active.value)
        for i in range(3)
    ]
    Project.objects.insert(projects)
    print(f"✓ Created {len(projects)} projects\n")
    
    # Example 18: Delete many (like Mongoose .deleteMany())
    print("18. Deleting test projects...")
    deleted_count = Project.objects(title__startswith="Project").delete()
    print(f"✓ Deleted {deleted_count} project(s)\n")
    
    print("=== Examples completed! ===")


if __name__ == "__main__":
    main()
