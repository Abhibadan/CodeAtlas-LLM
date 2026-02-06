from bullmq import Worker
from bullMQ import WorkerRegistry
from bullMQ.conection import connection_opts
from typing import Callable, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WorkerLoader:
    def __init__(
        self, 
        worker_name: str, 
        process_job: callable
    ):
        # BullMQ Worker expects connection options wrapped in a "connection" key
        worker_options = {"connection": connection_opts}
        
        self.__worker = Worker(worker_name, process_job, worker_options)
        # self.__worker.on("ready", lambda *args: print("✓ Worker is ready"))
        # self.__worker.on("completed", lambda *args: print(f"✓ Job {args[0].id if args else 'unknown'} completed"))
        # self.__worker.on("failed", lambda *args: print(f"✗ Job {args[0].id if args else 'unknown'} failed: {args[1] if len(args) > 1 else 'unknown error'}"))
        # self.__worker.on("error", lambda *args: print(f"❌ Worker error: {args[0] if args else 'unknown'}"))
        # self.__worker.on("progress", lambda *args: print(f"⏳ Job {args[0].id if args else 'unknown'} progress: {args[1] if len(args) > 1 else 'unknown'}"))
        # self.__worker.on("active", lambda *args: print(f"▶ Job {args[0].id if args else 'unknown'} active"))


    async def start_worker(self):
        """Start the worker with retry logic for BullMQ library bugs"""
        import asyncio

        
        # Retry loop to work around BullMQ library bug with empty task sets
        retry_count = 0
        while True:
            try:
                await self.__worker.run()
                print("Worker is running")
                break  # If run() completes normally, exit loop
            except ValueError as e:
                # Suppress the "Set of Tasks/Futures is empty" error from BullMQ library
                # This is a known library bug when no jobs are initially available
                if "Set of Tasks/Futures is empty" in str(e):
                    retry_count += 1
                    if retry_count == 1:
                        print("⚠ BullMQ library bug detected (empty task set)")
                    print(f"   Retrying in 5 seconds... (attempt #{retry_count})")
                    await asyncio.sleep(5)
                    # Continue the loop to retry
                else:
                    raise
            except KeyboardInterrupt:
                print("\n✓ Stopping worker...")
                break
            except Exception as e:
                print(f"❌ Worker error: {e}")
                import traceback
                traceback.print_exc()
                print("   Retrying in 5 seconds...")
                await asyncio.sleep(5)
                # Continue the loop to retry

    def on_ready(self,callback:callable):
        """Callback for when the worker is ready"""
        self.__worker.on("ready", callback)

    def on_completed(self, callback:callable):
        """Callback for when a job is completed"""
        logger.info("✓ Job completed")
        self.__worker.on("completed", callback)

    def on_failed(self, callback:callable):
        """Callback for when a job fails"""
        logger.info("✗ Job failed")
        self.__worker.on("failed", callback)

    def on_error(self, callback:callable):
        """Callback for when the worker encounters an error"""
        logger.info("❌ Worker error")
        self.__worker.on("error", callback)


    
    async def close_worker(self):
        """Close the worker and clean up resources"""
        print("Worker is closing...")
        await self.__worker.close()