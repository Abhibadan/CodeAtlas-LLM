

from kafka.admin import KafkaAdminClient,NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError
from kafka import KafkaProducer,KafkaConsumer
import logging
from typing import Optional
from config import kafka_config

logger = logging.getLogger(__name__)


class KafkaAdmin:
    """
    Kafka administration utilities
    """
    __admin_instance: Optional['KafkaAdmin'] = None
    __admin_client: Optional[KafkaAdminClient] = None
    __producers: list[KafkaProducer] = []
    __consumers: list[KafkaConsumer] = []
    
    def __new__(cls, *args, **kwargs):
        if cls.__admin_instance is None:
            cls.__admin_instance = super(KafkaAdmin, cls).__new__(cls)
            cls.__admin_instance.__initialized = False
        return cls.__admin_instance

    def __init__(self, *args, **kwargs):
        if self.__initialized:
            return
            
        try:
            self.__admin_client = KafkaAdminClient(
                bootstrap_servers=kafka_config["bootstrap_servers"],
                client_id='codeatlas-admin'
            )
            self.__initialized = True
            logger.info("Admin instance initialized")
        except KafkaError as e:
            logger.error(f"Failed to initialize Admin client: {e}")
            raise


    @property
    def admin_client(self) -> KafkaAdminClient:
        return self.__admin_client

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
            self.__admin_client.create_topics([topic], validate_only=False)
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
            self.__admin_client.delete_topics([topic_name])
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
            topics = self.__admin_client.list_topics()
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
        topics = self.__admin_client.list_topics()
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
            self.__producers.append(producer)
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
            self.__consumers.append(consumer)
            # logger.info(f"Kafka consumer created ")
            return consumer
        except KafkaError as e:
            # logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    def close_producer(self):
        """
        Close all Kafka producers
        """
        for producer in self.__producers:
            producer.close()
        self.__producers = []
    
    def close_consumer(self):
        """
        Close all Kafka consumers
        """
        for consumer in self.__consumers:
            consumer.close()
        self.__consumers = []
    
    def close_all(self):
        """
        Close all Kafka producers and consumers
        """
        self.close_producer()
        self.close_consumer()
        self.__admin_client.close()
        self.__instance = False
        self.__admin_client = None
        self.__producers = []
        self.__consumers = []