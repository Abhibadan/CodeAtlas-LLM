"""
Simple Queue Test - Single Worker
"""

from bullMQ import CreateQueue, WorkerRegistry
import asyncio

async def main():
    print("=== Adding Jobs to Queue ===\n")
    
    # Create email queue
    queue = CreateQueue(WorkerRegistry.EMAIL_WORKER.value)
    
    # Add first job
    print("Adding job 1...")
    await queue.add_job(
        job_name="test-email-1",
        job_data={
            "to": "user@example.com",
            "subject": "Test Email 1",
            "body": "This is the first test email"
        }
    )
    print("✓ Job 1 added\n")
    
    # Add second job
    print("Adding job 2...")
    await queue.add_job(
        job_name="test-email-2",
        job_data={
            "to": "admin@example.com",
            "subject": "Test Email 2",
            "body": "This is the second test email"
        }
    )
    print("✓ Job 2 added\n")
    
    print("=== All jobs added successfully ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
