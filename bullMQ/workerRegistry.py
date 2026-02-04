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
    
    # Example workers - replace these with your actual worker names
    EMAIL_WORKER = "email-worker"
    NOTIFICATION_WORKER = "notification-worker"
    DATA_PROCESSING_WORKER = "data-processing-worker"
    FILE_UPLOAD_WORKER = "file-upload-worker"
    REPORT_GENERATION_WORKER = "report-generation-worker"
    
    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get list of all worker names."""
        return [worker.value for worker in cls]
    
    @classmethod
    def has_worker(cls, worker_name: str) -> bool:
        """Check if a worker name exists in the registry."""
        return worker_name in cls._value2member_map_
