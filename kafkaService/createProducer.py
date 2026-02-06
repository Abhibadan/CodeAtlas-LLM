"""
Kafka Producer Helper
Provides utilities for producing messages to Kafka topics
"""
from kafka.errors import KafkaError
from typing import Any, Optional
from config import kafka_config
from kafkaService import KafkaAdmin
import json
import logging

logger = logging.getLogger(__name__)


class ProducerHelper(KafkaAdmin):
    """
    Helper class for Kafka message production
    """
    __producer = None
    def __init__(self):
        """
        Create a new Kafka producer instance (no caching to avoid stale connections)
        
        Returns:
            KafkaProducer: New Kafka producer instance
        """
        try:
            self.__producer = self._create_producer()
            logger.info("Kafka producer created")
        except KafkaError as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise
    
    def send_message(
        self,
        topic: str,
        message: Any,
        key: Optional[str] = None,
        partition: Optional[int] = None
    ) -> bool:
        """
        Send a message to a Kafka topic
        
        Args:
            topic: Topic name to send message to
            message: Message payload (will be JSON serialized)
            key: Message key for partitioning (optional)
            partition: Specific partition to send to (optional)
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            future = self.__producer.send(
                topic,
                value=message,
                key=key,
                partition=partition
            )
            
            # Block until message is sent or timeout
            record_metadata = future.get(timeout=30)
            
            logger.info(
                f"Message sent to topic '{topic}' "
                f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            return False
            
        finally:
            # Always close the producer to free resources
            if self.__producer:
                try:
                    self.__producer.flush()
                    self.__producer.close(timeout=5)
                except Exception:
                    pass  # Ignore errors during cleanup
    
    def send_batch(
        self,
        topic: str,
        messages: list[dict],
        key_field: Optional[str] = None
    ) -> tuple[int, int]:
        """
        Send a batch of messages to a Kafka topic
        
        Args:
            topic: Topic name to send messages to
            messages: List of message payloads
            key_field: Field name to use as message key (optional)
            
        Returns:
            tuple: (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for message in messages:
            try:
                key = message.get(key_field) if key_field else None
                
                future = self.__producer.send(
                    topic,
                    value=message,
                    key=key
                )
                
                # Non-blocking - just add callback
                future.add_callback(lambda _: None)
                future.add_errback(lambda e: logger.error(f"Error sending message: {e}"))
                
                successful += 1
                
            except Exception as e:
                logger.error(f"Failed to queue message: {e}")
                failed += 1
        
        # Flush all pending messages
        self.__producer.flush()
        
        logger.info(
            f"Batch send to topic '{topic}' completed: "
            f"{successful} successful, {failed} failed"
        )
        return successful, failed
    
    def flush(self):
        """
        Flush all pending messages from the producer
        """
        self.__producer.flush()
        logger.info("Producer flushed")
    def close(self):
        """
        Close the producer
        """
        self.__producer.close()
        logger.info("Producer closed")
