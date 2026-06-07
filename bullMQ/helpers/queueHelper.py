from bullmq import Queue
from bullMQ import WorkerRegistry
from bullMQ.conection import connection_opts

class CreateQueue:
    __queue = None
    def __init__(self, queue_name: str):
        self.__queue = Queue(queue_name, {"connection": connection_opts})
    
    async def add_job(self, job_name: str, job_data: dict):
        await self.__queue.add(job_name, job_data)