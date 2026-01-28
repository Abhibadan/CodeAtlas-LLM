import json
from bson import ObjectId
from dbModule.MongoDb import MongoDb
from dbModule.VectorDb import VectorDb
from config import config
from time import sleep
dbInstance = MongoDb()
projects = dbInstance.getCollection("projects")
projectmarkdowns = dbInstance.getCollection("projectmarkdowns")
projectdescriptions = dbInstance.getCollection("projectdescriptions")

pipeline = [
    {
        "$match": {
            "is_deleted": False
        }
    },
    {
        "$lookup": {
            "from": "projectmarkdowns",
            "localField": "_id",
            "foreignField": "projectId",
            "let": {"projectScanVersion": "$scan_version"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$scanVersion", "$$projectScanVersion"]}
                            ]
                        }
                    }
                }
            ],
            "as": "projectmarkdowns"
        }
    },
    {
        "$lookup": {
            "from": "projectdescriptions",
            "localField": "_id",
            "foreignField": "projectId",
            "let": {"projectScanVersion": "$scan_version"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$scanVersion", "$$projectScanVersion"]}
                            ]
                        }
                    }
                }
            ],
            "as": "projectdescriptions"
        }
    }
]
while True:
    for project in projects.aggregate(pipeline):
        vectorStore = VectorDb(config["CHROMA_HOST"],config["CHROMA_PORT"],project['title'],config["EMBEDDING_MODEL"],config["OPENAI_API_KEY"],config["OPENAI_BASE_URL"])
        if project.get("projectmarkdowns") or project.get("projectdescriptions"):
            vectorStore.clear_collection()

        if project.get("projectmarkdowns"):
            for markdown in project["projectmarkdowns"]:
                # Extract fields from markdown document
                file_path = markdown.get('filePath', '')
                file_name = markdown.get('fileName', file_path.split('/')[-1] if file_path else 'unknown')
                
                # Clean content for vector DB
                cleaned_content = markdown.get('cleanedContent', '').strip()
                
                # Skip empty documents
                if not cleaned_content:
                    continue
                
                # Extract related node IDs and match type
                related_node_ids = markdown.get('relatedNodeIds', [])
                match_type = markdown.get('matchType', 'unmatched')  # Default to 'unmatched' if not specified
                
                # Prepare metadata
                metadata = {
                    'filePath': file_path,
                    'fileName': file_name,
                    'relatedNodeIds': ",".join(related_node_ids),
                    'matchType': match_type,
                    'projectId': str(project['_id']),
                    'projectName': project['title'],
                    'scanVersion': markdown.get('scanVersion', project.get('scan_version')),
                    'type': 'markdown'
                }
                
                # Add document with metadata to vector store
                vectorStore.addDocument(content=cleaned_content, metadata=metadata)
        if project.get("projectdescriptions"):
            for description in project["projectdescriptions"]:
                # Extract fields from description document
                file_path = description.get('filePath', '')
                node_name = description.get('nodeName', 'unknown')
                
                # Clean content for vector DB - use description field for content
                cleaned_content = description.get('description', '').strip()
                
                # Skip empty documents
                if not cleaned_content:
                    continue
                
                # Extract related node IDs and match type
                related_node_ids = description.get('relatedNodeIds', [])
                match_type = description.get('matchType', 'unmatched')
                
                # Prepare metadata
                metadata = {
                    'filePath': file_path,
                    'fileName': node_name,
                    'nodeId': description.get('nodeId', ''),
                    'nodeName': description.get('nodeName', ''),
                    'nodeKind': description.get('nodeKind', ''),
                    'description': description.get('description', ''),
                    'fullComment': description.get('fullComment', ''),
                    'projectId': str(project['_id']),
                    'projectName': project['title'],
                    'scanVersion': description.get('scanVersion', project.get('scan_version')),
                    'type': 'description'
                }
                
                # Add document with metadata to vector store
                vectorStore.addDocument(content=cleaned_content, metadata=metadata)

        projectmarkdowns.delete_many({"projectId": project['_id'],"scanVersion": {"$lte": project.get('scan_version')}})
        projectdescriptions.delete_many({"projectId": project['_id'],"scanVersion": {"$lte": project.get('scan_version')}})
    sleep(300)

