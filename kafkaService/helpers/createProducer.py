"""
Kafka Producer Helper
Provides utilities for producing messages to Kafka topics
"""
from kafka.errors import KafkaError
import logging
from typing import Any, Optional
from ..connection import KafkaConnection

logger = logging.getLogger(__name__)


class ProducerHelper:
    """
    Helper class for Kafka message production
    """
    
    @staticmethod
    def send_message(
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
        producer = KafkaConnection.get_producer()
        
        try:
            future = producer.send(
                topic,
                value=message,
                key=key,
                partition=partition
            )
            
            # Block until message is sent or timeout
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Message sent to topic '{topic}' "
                f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            return False
    
    @staticmethod
    def send_batch(
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
        producer = KafkaConnection.get_producer()
        successful = 0
        failed = 0
        
        for message in messages:
            try:
                key = message.get(key_field) if key_field else None
                
                future = producer.send(
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
        producer.flush()
        
        logger.info(
            f"Batch send to topic '{topic}' completed: "
            f"{successful} successful, {failed} failed"
        )
        return successful, failed
    
    @staticmethod
    def flush():
        """
        Flush all pending messages from the producer
        """
        producer = KafkaConnection.get_producer()
        producer.flush()
        logger.info("Producer flushed")
