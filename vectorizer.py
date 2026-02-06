import json
import sys
from bson import ObjectId
from dbModule import init_db, Project, Markdown, Description
from dbModule.VectorDb import VectorDb
from config import chroma_config, google_config, mongo_config
from bullMQ import WorkerLoader, WorkerRegistry
from kafkaService import ProducerHelper,TopicRegistry
import asyncio
import signal
import logging
logger = logging.getLogger(__name__)

# Initialize MongoDB connection using MongoEngine
init_db(database_name=mongo_config["db"], host=mongo_config["uri"])


async def process_vectorizer_job(job, job_token):
    """Process a vectorizer job"""
    try:

        # Extract job data
        job_data = job.data

        project = Project.find_by_id(ObjectId(job_data["projectId"]))
        
        print("project parsing", project)

        # Get markdowns and descriptions for this project with matching scanVersion
        markdowns = Markdown.objects(
            projectId=project.id,
            scanVersion=project.scan_version
        )

        print("markdowns count",markdowns.count())
        
        descriptions = Description.objects(
            projectId=project.id,
            scanVersion=project.scan_version
        )

        print("descriptions count",descriptions.count())
        
        vectorStore = None
        # Clear collection if there are new markdowns or descriptions
        if markdowns.count() > 0 or descriptions.count() > 0:
            # Initialize vector store for this project
            print("Initializing vector store for project", project.projectName)
            vectorStore = VectorDb(
                chroma_config["host"],
                chroma_config["port"],
                project.uuid,  # Using backward compatible property
                google_config["embedding_model"],
                google_config["api_key"]
            )
            vectorStore.clear_collection()
        else:
            print("No new markdowns or descriptions for project", project.projectName)
            return
        
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
                continue
            
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
        
        # Job will be automatically marked as completed when function returns
        logger.info(f"✓ Job {job.id} processed successfully!")
        return True
    except Exception as e:
        # Job will be automatically marked as failed when exception is raised
        print(f"✗ Error processing job {job.id}: {e}")
        raise 


def vectorixation_completed_callback(job, job_token):
    """Callback function to be called when a vectorization job is completed"""
    try:
        print("Sending vectorization completed message...")
        # Send a message to Kafka to notify the frontend
        producer = ProducerHelper()
        producer.send_message(
            topic=TopicRegistry.CODEATLAS_LLM_EVENTS.value,
            message={
                "type": "vectorization_completed",
                "projectId": job.data["projectId"],
                "jobId": job.id
            }
        )
        producer.close()
        logger.info(f"✓ Sent vectorization completed event for project {job.data['projectId']}")
    except Exception as e:
        logger.error(f"Error sending vectorization completed message: {e}")

async def main():
    """Main async function to properly handle worker lifecycle"""
    worker_loader = WorkerLoader(WorkerRegistry.VECTORIZER_WORKER.value, process_vectorizer_job)
    try:
        # Initialize worker inside async context
        worker_loader.on_completed(vectorixation_completed_callback)
        worker_loader.on_failed(lambda job, error: logger.error(f"✗ Job {job.id} failed: {error}"))
        worker_loader.on_error(lambda error, job: logger.error(f"❌ Worker error: {error}"))
        worker_loader.on_ready(lambda: logger.info("✓ Worker is ready"))
        logger.info("Starting worker...")
        await worker_loader.start_worker()
    finally:
        # Clean up resources
        print("Cleaning up resources...")

        await worker_loader.close_worker()
        # signal.signal(signal.SIGINT, lambda sig, frame: print("\n✓ Worker stopped"))
        # signal.signal(signal.SIGTERM, lambda sig, frame: print("\n✓ Worker stopped"))


if __name__ == "__main__":
    """Entry point for daemon mode"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n✓ Worker stopped")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

