"""
Kafka Consumer Helper
Provides utilities for consuming messages from Kafka topics
"""

from kafka.errors import KafkaError
from kafkaService import KafkaAdmin
import logging
from typing import Callable, Optional, Any
from config import kafka_config

logger = logging.getLogger(__name__)


class ConsumerHelper(KafkaAdmin):
    """
    Helper class for Kafka message consumption
    """
    def __init__(self, topics: list[str]):
        try:
            self.__consumer = self._create_consumer(topics)
        except KafkaError as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise

    def consume_messages(
        self,
        message_handler: Callable[[Any], None],
        max_messages: Optional[int] = None,
    ):
        """
        Consume messages from Kafka topics
        
        Args:
            topics: List of topics to consume from
            message_handler: Callback function to process each message
            group_id: Consumer group ID (optional)
            max_messages: Maximum number of messages to consume (None for infinite)
        """
        messages_consumed = 0
        
        try:
            for message in self.__consumer:
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
            self.__consumer.close()
            logger.info(f"Consumer closed. Total messages consumed: {messages_consumed}")