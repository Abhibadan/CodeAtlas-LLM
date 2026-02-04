"""
Kafka Admin Module
Provides utilities for managing Kafka topics and configurations
"""
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError
import logging
from typing import Optional
from .connection import KafkaConnection

logger = logging.getLogger(__name__)


class KafkaAdmin:
    """
    Kafka administration utilities
    """
    
    @staticmethod
    def create_topic(
        topic_name: str,
        num_partitions: int = 1,
        replication_factor: int = 1,
        topic_configs: Optional[dict] = None
    ) -> bool:
        """
        Create a new Kafka topic
        
        Args:
            topic_name: Name of the topic to create
            num_partitions: Number of partitions (default: 1)
            replication_factor: Replication factor (default: 1)
            topic_configs: Additional topic configurations
            
        Returns:
            bool: True if topic was created, False if already exists
        """
        admin_client = KafkaConnection.get_admin_client()
        
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            topic_configs=topic_configs or {}
        )
        
        try:
            admin_client.create_topics([topic], validate_only=False)
            logger.info(f"Topic '{topic_name}' created successfully")
            return True
        except TopicAlreadyExistsError:
            logger.warning(f"Topic '{topic_name}' already exists")
            return False
        except KafkaError as e:
            logger.error(f"Failed to create topic '{topic_name}': {e}")
            raise
    
    @staticmethod
    def delete_topic(topic_name: str) -> bool:
        """
        Delete a Kafka topic
        
        Args:
            topic_name: Name of the topic to delete
            
        Returns:
            bool: True if topic was deleted
        """
        admin_client = KafkaConnection.get_admin_client()
        
        try:
            admin_client.delete_topics([topic_name])
            logger.info(f"Topic '{topic_name}' deleted successfully")
            return True
        except KafkaError as e:
            logger.error(f"Failed to delete topic '{topic_name}': {e}")
            raise
    
    @staticmethod
    def list_topics() -> set:
        """
        List all available Kafka topics
        
        Returns:
            set: Set of topic names
        """
        admin_client = KafkaConnection.get_admin_client()
        
        try:
            topics = admin_client.list_topics()
            logger.info(f"Found {len(topics)} topics")
            return topics
        except KafkaError as e:
            logger.error(f"Failed to list topics: {e}")
            raise
    
    @staticmethod
    def topic_exists(topic_name: str) -> bool:
        """
        Check if a topic exists
        
        Args:
            topic_name: Name of the topic to check
            
        Returns:
            bool: True if topic exists
        """
        topics = KafkaAdmin.list_topics()
        return topic_name in topics
