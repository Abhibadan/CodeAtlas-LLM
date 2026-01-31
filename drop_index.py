"""
Script to drop the conflicting uuid_1 index from the projects collection.
Run this once, then run vectorizer.py again.
"""
from pymongo import MongoClient
from config import config

# Connect to MongoDB
client = MongoClient(config["MONGO_URI"])
db = client[config["MONGO_DB"]]

# Drop the conflicting index
try:
    db.projects.drop_index("uuid_1")
    print("✓ Successfully dropped index 'uuid_1' from 'projects' collection")
except Exception as e:
    print(f"Note: {e}")

# List remaining indexes
print("\nRemaining indexes on 'projects' collection:")
for index in db.projects.list_indexes():
    print(f"  - {index['name']}: {index.get('key')}")

client.close()
print("\n✓ Done! You can now run vectorizer.py")
