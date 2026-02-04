"""
Kafka Consumer Helper
Provides utilities for consuming messages from Kafka topics
"""
from kafka.errors import KafkaError
import logging
from typing import Callable, Optional, Any
from ..connection import KafkaConnection

logger = logging.getLogger(__name__)


class ConsumerHelper:
    """
    Helper class for Kafka message consumption
    """
    
    @staticmethod
    def consume_messages(
        topics: list[str],
        message_handler: Callable[[Any], None],
        group_id: Optional[str] = None,
        max_messages: Optional[int] = None,
        timeout_ms: int = 1000
    ):
        """
        Consume messages from Kafka topics
        
        Args:
            topics: List of topics to consume from
            message_handler: Callback function to process each message
            group_id: Consumer group ID (optional)
            max_messages: Maximum number of messages to consume (None for infinite)
            timeout_ms: Poll timeout in milliseconds
        """
        consumer = KafkaConnection.get_consumer(topics, group_id)
        messages_consumed = 0
        
        try:
            logger.info(f"Starting consumer for topics: {topics}")
            
            for message in consumer:
                try:
                    logger.debug(
                        f"Received message from topic '{message.topic}' "
                        f"[partition: {message.partition}, offset: {message.offset}]"
                    )
                    
                    # Process the message using the handler
                    message_handler(message.value)
                    messages_consumed += 1
                    
                    # Check if we've reached the max message limit
                    if max_messages and messages_consumed >= max_messages:
                        logger.info(f"Reached max messages limit: {max_messages}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue consuming next message
                    continue
                    
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
            raise
        finally:
            consumer.close()
            logger.info(f"Consumer closed. Total messages consumed: {messages_consumed}")
    
    @staticmethod
    def consume_with_context(
        topics: list[str],
        message_handler: Callable[[dict], None],
        group_id: Optional[str] = None
    ):
        """
        Consume messages with additional context (topic, partition, offset)
        
        Args:
            topics: List of topics to consume from
            message_handler: Callback function that receives message context
            group_id: Consumer group ID (optional)
        """
        consumer = KafkaConnection.get_consumer(topics, group_id)
        
        try:
            logger.info(f"Starting consumer with context for topics: {topics}")
            
            for message in consumer:
                try:
                    context = {
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "timestamp": message.timestamp,
                        "key": message.key,
                        "value": message.value,
                    }
                    
                    message_handler(context)
                    
                except Exception as e:
                    logger.error(f"Error processing message with context: {e}")
                    continue
                    
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
            raise
        finally:
            consumer.close()
            logger.info("Consumer with context closed")
    
    @staticmethod
    def peek_messages(
        topics: list[str],
        count: int = 10,
        group_id: Optional[str] = None
    ) -> list[Any]:
        """
        Peek at the first N messages without committing offsets
        
        Args:
            topics: List of topics to peek from
            count: Number of messages to peek
            group_id: Consumer group ID (optional)
            
        Returns:
            list: List of message values
        """
        # Create a temporary consumer with auto-commit disabled
        from kafka import KafkaConsumer
        from config import kafka_config
        import json
        
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=kafka_config["bootstrap_servers"],
            group_id=group_id or kafka_config["group_id"],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
            enable_auto_commit=False,  # Don't commit offsets
            auto_offset_reset='earliest',
        )
        
        messages = []
        
        try:
            for i, message in enumerate(consumer):
                if i >= count:
                    break
                messages.append(message.value)
                
        finally:
            consumer.close()
            
        logger.info(f"Peeked {len(messages)} messages from topics: {topics}")
        return messages
