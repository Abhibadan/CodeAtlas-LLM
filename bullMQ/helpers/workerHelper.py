from bullmq import Worker
from bullMQ import WorkerRegistry
from bullMQ.conection import connection_opts
from typing import Callable, Dict, Any, Optional


class WorkerLoader:
    """
    Worker Loader with support for options and event listeners.
    
    Example usage:
        worker = WorkerLoader(
            worker_name=WorkerRegistry.EMAIL_WORKER,
            process_job=my_process_function,
            worker_options={
                "concurrency": 5,
                "limiter": {
                    "max": 10,
                    "duration": 1000
                }
            }
        )
        
        # Add event listeners
        worker.on_completed(lambda job, result: print(f"Job {job.id} completed"))
        worker.on_failed(lambda job, error: print(f"Job {job.id} failed: {error}"))
    """
    
    def __init__(
        self, 
        worker_name: str, 
        process_job: callable,
        worker_options: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize worker with optional configuration.
        
        Args:
            worker_name: Name of the worker queue
            process_job: Async function to process jobs
            worker_options: Optional worker configuration including:
                - concurrency: Number of jobs to process in parallel (default: 1)
                - limiter: Rate limiting config {"max": 10, "duration": 1000}
                - autorun: Whether to automatically start processing (default: True)
                - removeOnComplete: Remove jobs on completion (default: False)
                - removeOnFail: Remove jobs on failure (default: False)
        """
        # Merge connection options with worker options
        options = {"connection": connection_opts}
        
        if worker_options:
            options.update(worker_options)
        
        self.__worker = Worker(worker_name, process_job, options)
    
    def get_worker(self):
        """Get the underlying worker instance"""
        return self.__worker

    async def close_worker(self):
        """Close the worker and clean up resources"""
        await self.__worker.close()