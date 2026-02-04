
from kafkaService import KafkaConnection, KafkaAdmin, ProducerHelper, ConsumerHelper
from kafkaService.topicsRegistry import TopicRegistry
import logging

def example_peek_messages():
    """Example: Peek at messages without consuming them"""
    print("\n=== Peek Messages Example ===")
    
    # Peek at the first 5 messages
    messages = ConsumerHelper.consume_messages(
        topics=[TopicRegistry.CODEATLAS_LLM_EVENTS.value],
        message_handler=lambda msg: print(msg),
    )
    
    print(f"Peeked {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"{i}. {msg}")

example_peek_messages()