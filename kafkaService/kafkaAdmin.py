

from kafka.admin import KafkaAdminClient,NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError
from kafka import KafkaProducer,KafkaConsumer
import logging
import json
from typing import Optional
from config import kafka_config

logger = logging.getLogger(__name__)

class _kafkaStore:
    __store_instance: Optional['_kafkaStore'] = None
    __store_client: Optional[KafkaAdminClient] = None
    __consumers: list[KafkaConsumer] = []
    
    def __new__(cls, *args, **kwargs):
        if cls.__store_instance is None:
            cls.__store_instance = super(_kafkaStore, cls).__new__(cls)
            cls.__store_instance.__initialized = False
        return cls.__store_instance

    def __init__(self, *args, **kwargs):
        if self.__initialized:
            return
            
        try:
            self.__store_client = KafkaAdminClient(
                bootstrap_servers=kafka_config["bootstrap_servers"],
                client_id='codeatlas-store'
            )
            self.__initialized = True
            logger.info("Store instance initialized")
        except KafkaError as e:
            logger.error(f"Failed to initialize Store client: {e}")
            raise

    @property
    def store_client(self) -> KafkaAdminClient:
        return self.__store_client
    
    def store_producer(self,produder:KafkaProducer):
        self.__producers.append(produder)
        
    def store_consumer(self,consumer:KafkaConsumer):
        self.__consumers.append(consumer)
        
    def store_producers(self,producers:list[KafkaProducer]):
        self.__producers.extend(producers)
        
    def store_consumers(self,consumers:list[KafkaConsumer]):
        self.__consumers.extend(consumers)
        
    def close(self):
        for consumer in self.__consumers:
            consumer.close()
        self.__store_client.close()

class KafkaAdmin:
    """
    Kafka administration utilities
    """
    __kafkaStore = _kafkaStore()

    def create_topic(
        self,
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
        
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            topic_configs=topic_configs or {}
        )
        
        try:
            self.__kafkaStore.store_client.create_topics([topic], validate_only=False)
            logger.info(f"Topic '{topic_name}' created successfully")
            return True
        except TopicAlreadyExistsError:
            logger.warning(f"Topic '{topic_name}' already exists")
            return False
        except KafkaError as e:
            logger.error(f"Failed to create topic '{topic_name}': {e}")
            raise
    
    def delete_topic(self,topic_name: str) -> bool:
        """
        Delete a Kafka topic
        
        Args:
            topic_name: Name of the topic to delete
            
        Returns:
            bool: True if topic was deleted
        """
        
        try:
            self.__kafkaStore.store_client.delete_topics([topic_name])
            logger.info(f"Topic '{topic_name}' deleted successfully")
            return True
        except KafkaError as e:
            logger.error(f"Failed to delete topic '{topic_name}': {e}")
            raise
    
    def list_topics(self) -> set:
        """
        List all available Kafka topics
        
        Returns:
            set: Set of topic names
        """
        
        try:
            topics = self.__kafkaStore.store_client.list_topics()
            logger.info(f"Found {len(topics)} topics")
            return topics
        except KafkaError as e:
            logger.error(f"Failed to list topics: {e}")
            raise
    
    def topic_exists(self,topic_name: str) -> bool:
        """
        Check if a topic exists
        
        Args:
            topic_name: Name of the topic to check
            
        Returns:
            bool: True if topic exists
        """
        topics = self.__kafkaStore.store_client.list_topics()
        return topic_name in topics
    
    def _create_producer(self) -> KafkaProducer:
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_config["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=1,
                request_timeout_ms=30000,  # 30 seconds
                api_version_auto_timeout_ms=5000,  # 5 seconds for version detection
            )
            self.__kafkaStore.store_producer(producer)
            return producer
        except KafkaError as e:
            # logger.error(f"Failed to create producer: {e}")
            raise
    
    def _create_consumer(self,topics: list[str]) -> KafkaConsumer:
        try:
            consumer = KafkaConsumer(
                    *topics,
                    bootstrap_servers=kafka_config["bootstrap_servers"],
                    group_id=kafka_config["group_id"],
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                    key_deserializer=lambda k: k.decode('utf-8') if k else None,
                    auto_offset_reset='earliest',  # Start from beginning if no offset
                    enable_auto_commit=True,
                    auto_commit_interval_ms=1000,
                )
            self.__kafkaStore.store_consumer(consumer)
            # logger.info(f"Kafka consumer created ")
            return consumer
        except KafkaError as e:
            # logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    def close_all(self):
        """
        Close all Kafka producers and consumers
        """
        self.__kafkaStore.close()