import json
from bson import ObjectId
from dbModule import init_db, Project, Markdown, Description
from dbModule.VectorDb import VectorDb
from config import chroma_config, google_config, mongo_config
from bullMQ import WorkerLoader, WorkerRegistry
import asyncio

# Initialize MongoDB connection using MongoEngine
init_db(database_name=mongo_config["MONGO_DB"], host=mongo_config["MONGO_URI"])


async def process_vectorizer_job(job, job_token):
    """Process a vectorizer job"""
    try:
        # Extract job data
        job_data = job.data

        project = Project.find_by_id(ObjectId(job_data["projectId"]))
        
        # Get markdowns and descriptions for this project with matching scanVersion
        markdowns = Markdown.objects(
            projectId=project.id,
            scanVersion=project.scan_version
        )

        # print("markdowns count",markdowns.count())
        
        descriptions = Description.objects(
            projectId=project.id,
            scanVersion=project.scan_version
        )

        # print("descriptions count",descriptions.count())
        
        vectorStore = None
        # Clear collection if there are new markdowns or descriptions
        if markdowns.count() > 0 or descriptions.count() > 0:
            # Initialize vector store for this project
            # print("Initializing vector store for project", project.projectName)
            vectorStore = VectorDb(
                chroma_config["host"],
                chroma_config["port"],
                project.uuid,  # Using backward compatible property
                google_config["EMBEDDING_MODEL"],
                google_config["GOOGLE_API_KEY"]
            )
            vectorStore.clear_collection()
        else:
            # print("No new markdowns or descriptions for project", project.projectName)
            continue
        
        # Process markdowns
        for markdown in markdowns:
            # Extract fields from markdown document
            file_path = markdown.filePath or ''
            file_name = markdown.fileName or (file_path.split('/')[-1] if file_path else 'unknown')
            
            # Clean content for vector DB
            cleaned_content = (markdown.content or '').strip()
            
            # Skip empty documents
            if not cleaned_content:
                continue
            
            # Extract related node IDs and match type
            related_node_ids = markdown.relatedNodeIds or []
            match_type = markdown.matchType or 'unmatched'
            
            # Prepare metadata
            metadata = {
                'filePath': file_path,
                'fileName': file_name,
                'relatedNodeIds': ",".join(related_node_ids) if isinstance(related_node_ids, list) else str(related_node_ids or ""),
                'matchType': match_type,
                'projectId': str(project.id),
                'projectName': project.projectName,
                'scanVersion': markdown.scanVersion or project.scan_version,
                'type': 'markdown'
            }
            
            # Add document with metadata to vector store
            vectorStore.addDocument(content=cleaned_content, metadata=metadata)
        
        # Process descriptions
        for description in descriptions:
            # Extract fields from description document
            file_path = description.filePath or ''
            file_name = description.fileName or (file_path.split('/')[-1] if file_path else 'unknown')
            
            # Clean content for vector DB
            cleaned_content = (description.content or '').strip()
            
            # Skip empty documents
            if not cleaned_content:
                return
            
            # Extract related node IDs and match type
            related_node_ids = description.relatedNodeIds or []
            match_type = description.matchType or 'unmatched'
            
            # Prepare metadata
            metadata = {
                'filePath': file_path,
                'fileName': file_name,
                'relatedNodeIds': ",".join(related_node_ids) if isinstance(related_node_ids, list) else str(related_node_ids or ""),
                'matchType': match_type,
                'projectId': str(project.id),
                'projectName': project.projectName,
                'scanVersion': description.scanVersion or project.scan_version,
                'type': 'description'
            }
            
            # Add document with metadata to vector store
            vectorStore.addDocument(content=cleaned_content, metadata=metadata)
        
        # Delete old markdowns and descriptions (scanVersion less than or equal to current)
        # Using MongoEngine's delete method
        Markdown.objects(
            projectId=project.id,
            scanVersion__lte=project.scan_version
        ).delete()
        
        Description.objects(
            projectId=project.id,
            scanVersion__lte=project.scan_version
        ).delete()
        
        # Mark job as completed
        await job.update(status='completed')
        
        print(f"✓ Job {job.id} processed successfully!")
        
    except Exception as e:
        # Mark job as failed
        await job.update(status='failed', error=str(e))
        
        print(f"✗ Error processing job {job.id}: {e}")
        raise


worker = WorkerLoader(WorkerRegistry.VECTORIZER_WORKER, process_vectorizer_job, {
    "autorun": True,
    "removeOnComplete": {
        "age": 3600,
        "count": 500 
    },
    "removeOnFail": {
        "age": 86400,
        "count": 1000
    },
    "concurrency": 1,
    "limiter": {
        "max": 1,
        "duration": 1000
    },
    "settings": {
        "attempts": 3,
        "backoff": {
            "type": "exponential",
            "delay": 1000
        }
    }
})

if __name__ == "__main__":
    """Entry point for daemon mode"""
    try:
        worker.on("ready",lambda: print("Worker is ready"))
        worker.on("completed",lambda job, result: print(f"Job {job.id} completed"))
        worker.on("failed",lambda job, error: print(f"Job {job.id} failed: {error}"))
        worker.on("error",lambda error: print(f"Worker error: {error}"))
        worker.on("progress",lambda job, progress: print(f"Job {job.id} progress: {progress}"))
        worker.on("active",lambda job: print(f"Job {job.id} active"))
        print("Worker is starting...")
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        print("\n✓ Worker stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

# # Main processing loop
# while True:
#     # Query active projects using MongoEngine ODM
#     projects = Project.objects(is_deleted=False)
#     for project in projects:
#         # Get markdowns and descriptions for this project with matching scanVersion
#         markdowns = Markdown.objects(
#             projectId=project.id,
#             scanVersion=project.scan_version
#         )

#         # print("markdowns count",markdowns.count())
        
#         descriptions = Description.objects(
#             projectId=project.id,
#             scanVersion=project.scan_version
#         )

#         # print("descriptions count",descriptions.count())
        
#         vectorStore = None
#         # Clear collection if there are new markdowns or descriptions
#         if markdowns.count() > 0 or descriptions.count() > 0:
#             # Initialize vector store for this project
#             # print("Initializing vector store for project", project.projectName)
#             vectorStore = VectorDb(
#                 chroma_config["host"],
#                 chroma_config["port"],
#                 project.uuid,  # Using backward compatible property
#                 google_config["EMBEDDING_MODEL"],
#                 google_config["GOOGLE_API_KEY"]
#             )
#             vectorStore.clear_collection()
#         else:
#             # print("No new markdowns or descriptions for project", project.projectName)
#             continue
        
#         # Process markdowns
#         for markdown in markdowns:
#             # Extract fields from markdown document
#             file_path = markdown.filePath or ''
#             file_name = markdown.fileName or (file_path.split('/')[-1] if file_path else 'unknown')
            
#             # Clean content for vector DB
#             cleaned_content = (markdown.content or '').strip()
            
#             # Skip empty documents
#             if not cleaned_content:
#                 continue
            
#             # Extract related node IDs and match type
#             related_node_ids = markdown.relatedNodeIds or []
#             match_type = markdown.matchType or 'unmatched'
            
#             # Prepare metadata
#             metadata = {
#                 'filePath': file_path,
#                 'fileName': file_name,
#                 'relatedNodeIds': ",".join(related_node_ids) if isinstance(related_node_ids, list) else str(related_node_ids or ""),
#                 'matchType': match_type,
#                 'projectId': str(project.id),
#                 'projectName': project.projectName,
#                 'scanVersion': markdown.scanVersion or project.scan_version,
#                 'type': 'markdown'
#             }
            
#             # Add document with metadata to vector store
#             vectorStore.addDocument(content=cleaned_content, metadata=metadata)
        
#         # Process descriptions
#         for description in descriptions:
#             # Extract fields from description document
#             file_path = description.filePath or ''
#             file_name = description.fileName or (file_path.split('/')[-1] if file_path else 'unknown')
            
#             # Clean content for vector DB
#             cleaned_content = (description.content or '').strip()
            
#             # Skip empty documents
#             if not cleaned_content:
#                 continue
            
#             # Extract related node IDs and match type
#             related_node_ids = description.relatedNodeIds or []
#             match_type = description.matchType or 'unmatched'
            
#             # Prepare metadata
#             metadata = {
#                 'filePath': file_path,
#                 'fileName': file_name,
#                 'relatedNodeIds': ",".join(related_node_ids) if isinstance(related_node_ids, list) else str(related_node_ids or ""),
#                 'matchType': match_type,
#                 'projectId': str(project.id),
#                 'projectName': project.projectName,
#                 'scanVersion': description.scanVersion or project.scan_version,
#                 'type': 'description'
#             }
            
#             # Add document with metadata to vector store
#             vectorStore.addDocument(content=cleaned_content, metadata=metadata)
        
#         # Delete old markdowns and descriptions (scanVersion less than or equal to current)
#         # Using MongoEngine's delete method
#         Markdown.objects(
#             projectId=project.id,
#             scanVersion__lte=project.scan_version
#         ).delete()
        
#         Description.objects(
#             projectId=project.id,
#             scanVersion__lte=project.scan_version
#         ).delete()
    
#     # Sleep for 5 minutes before next iteration
#     sleep(300)


