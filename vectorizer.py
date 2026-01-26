import json
from bson import ObjectId
from dbModule.MongoDb import MongoDb
from dbModule.VectorDb import VectorDb
from config import config
from time import sleep
dbInstance = MongoDb()

# while True:
projects,markdowns,descriptions= dbInstance.getCollection("projects"),dbInstance.getCollection("markdowns"),dbInstance.getCollection("descriptions")

pipeline = [
    {
        "$match": {
            "isDeleted": False
        }
    },
    {
        "$lookup": {
            "from": "markdowns",
            "localField": "_id",
            "foreignField": "projectId",
            "let": {"projectScanVersion": "$scanVersion"},
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
            "as": "markdowns"
        }
    },
    {
        "$lookup": {
            "from": "descriptions",
            "localField": "_id",
            "foreignField": "projectId",
            "let": {"projectScanVersion": "$scanVersion"},
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
            "as": "descriptions"
        }
    }
]

for project in projects.aggregate(pipeline):
    print(project['projectName'])
    vectorStore = VectorDb(config["CHROMA_HOST"],config["CHROMA_PORT"],project['projectName'],config["EMBEDDING_MODEL"],config["GOOGLE_API_KEY"])
    if project.get("markdowns") or project.get("descriptions"):
        print("Clear collection")
        vectorStore.clear_collection()

    if project.get("markdowns"):
        for markdown in project["markdowns"]:
            # Extract fields from markdown document
            file_path = markdown.get('filePath', '')
            file_name = markdown.get('fileName', file_path.split('/')[-1] if file_path else 'unknown')
            
            # Clean content for vector DB
            cleaned_content = markdown.get('content', '').strip()
            
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
                'relatedNodeIds': json.dumps(related_node_ids) if isinstance(related_node_ids, list) else str(related_node_ids),
                'matchType': match_type,
                'projectId': str(project['_id']),
                'projectName': project['projectName'],
                'scanVersion': markdown.get('scanVersion', project.get('scanVersion')),
                'type': 'markdown'
            }
            
            print("metadata",metadata)
            # Add document with metadata to vector store
            vectorStore.addDocument(content=cleaned_content, metadata=metadata)
            sleep(1)    
    if project.get("descriptions"):
        for description in project["descriptions"]:
            # Extract fields from description document
            file_path = description.get('filePath', '')
            file_name = description.get('fileName', file_path.split('/')[-1] if file_path else 'unknown')
            
            # Clean content for vector DB
            cleaned_content = description.get('content', '').strip()
            
            # Skip empty documents
            if not cleaned_content:
                continue
            
            # Extract related node IDs and match type
            related_node_ids = description.get('relatedNodeIds', [])
            match_type = description.get('matchType', 'unmatched')
            
            # Prepare metadata
            metadata = {
                'filePath': file_path,
                'fileName': file_name,
                'relatedNodeIds': json.dumps(related_node_ids) if isinstance(related_node_ids, list) else str(related_node_ids),
                'matchType': match_type,
                'projectId': str(project['_id']),
                'projectName': project['projectName'],
                'scanVersion': description.get('scanVersion', project.get('scanVersion')),
                'type': 'description'
            }
            
            # Add document with metadata to vector store
            vectorStore.addDocument(content=cleaned_content, metadata=metadata)
            sleep(1)

    print(markdowns.delete_many({"projectId": project['_id'],"scanVersion": {"$lte": project.get('scanVersion')}}))
    print(descriptions.delete_many({"projectId": project['_id'],"scanVersion": {"$lte": project.get('scanVersion')}}))
    

