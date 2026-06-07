"""
Worker Registry
Enum containing all available worker names for the BullMQ system.
"""

from enum import Enum


class WorkerRegistry(str, Enum):
    """
    Enum of all available worker names.
    Add new worker names here when creating new workers.
    """
    
    VECTORIZER_WORKER = "VECTORIZER_WORKER"
    
    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get list of all worker names."""
        return [worker.value for worker in cls]
    
    @classmethod
    def has_worker(cls, worker_name: str) -> bool:
        """Check if a worker name exists in the registry."""
        return worker_name in cls._value2member_map_
