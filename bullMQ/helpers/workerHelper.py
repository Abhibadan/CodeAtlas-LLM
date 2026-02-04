from bullmq import Worker
from bullMQ import WorkerRegistry
from bullMQ.conection import connection_opts

class WorkerLoader:
    
    def __init__(self, worker_name: str, process_job: callable):
        self.__worker = Worker(worker_name, process_job, {"connection": connection_opts})
    
    def get_worker(self):
        """Get the underlying worker instance"""
        return self.__worker

    async def close_worker(self):
        await self.__worker.close()