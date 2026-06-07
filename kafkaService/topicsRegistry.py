"""
Topic Registry
Enum containing all available topics for the Kafka system.
"""

from enum import Enum


class TopicRegistry(str, Enum):
    """
    Enum of all available topics.
    Add new topics here when creating new topics.
    """
    
    CODEATLAS_LLM_EVENTS = "codeatlas-llm-events"
    
    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get list of all topics."""
        return [topic.value for topic in cls]
    
    @classmethod
    def has_topic(cls, topic_name: str) -> bool:
        """Check if a topic name exists in the registry."""
        return topic_name in cls._value2member_map_
