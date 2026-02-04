"""
Kafka Connection Module
Manages Kafka producer and consumer connections
"""
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient
from kafka.errors import KafkaError
import json
import logging
from typing import Optional
from config import kafka_config

logger = logging.getLogger(__name__)


class KafkaConnection:
    """
    Singleton class to manage Kafka connections
    """
    _producer: Optional[KafkaProducer] = None
    _admin_client: Optional[KafkaAdminClient] = None
    
    @classmethod
    def get_producer(cls) -> KafkaProducer:
        """
        Get or create a Kafka producer instance
        
        Returns:
            KafkaProducer: Configured Kafka producer
        """
        if cls._producer is None:
            try:
                cls._producer = KafkaProducer(
                    bootstrap_servers=kafka_config["bootstrap_servers"],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas to acknowledge
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                )
                logger.info("Kafka producer created successfully")
            except KafkaError as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise
        return cls._producer
    
    @classmethod
    def get_consumer(cls, topics: list[str], group_id: Optional[str] = None) -> KafkaConsumer:
        """
        Create a new Kafka consumer instance
        
        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID (optional, uses default from config)
            
        Returns:
            KafkaConsumer: Configured Kafka consumer
        """
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=kafka_config["bootstrap_servers"],
                group_id=group_id or kafka_config["group_id"],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',  # Start from beginning if no offset
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
            )
            logger.info(f"Kafka consumer created for topics: {topics}")
            return consumer
        except KafkaError as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    @classmethod
    def get_admin_client(cls) -> KafkaAdminClient:
        """
        Get or create a Kafka admin client instance
        
        Returns:
            KafkaAdminClient: Configured Kafka admin client
        """
        if cls._admin_client is None:
            try:
                cls._admin_client = KafkaAdminClient(
                    bootstrap_servers=kafka_config["bootstrap_servers"],
                    client_id='codeatlas-admin'
                )
                logger.info("Kafka admin client created successfully")
            except KafkaError as e:
                logger.error(f"Failed to create Kafka admin client: {e}")
                raise
        return cls._admin_client
    
    @classmethod
    def close_producer(cls):
        """Close the producer connection"""
        if cls._producer:
            cls._producer.close()
            cls._producer = None
            logger.info("Kafka producer closed")
    
    @classmethod
    def close_admin_client(cls):
        """Close the admin client connection"""
        if cls._admin_client:
            cls._admin_client.close()
            cls._admin_client = None
            logger.info("Kafka admin client closed")
