"""
Kafka Service Usage Examples
Demonstrates how to use the Kafka service module
"""
from kafkaService import KafkaConnection, KafkaAdmin, ProducerHelper, ConsumerHelper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_admin_operations():
    """Example: Create and manage Kafka topics"""
    print("\n=== Admin Operations Example ===")
    
    # Create a topic
    KafkaAdmin.create_topic(
        topic_name="codeatlas-events",
        num_partitions=3,
        replication_factor=1
    )
    
    # Check if topic exists
    exists = KafkaAdmin.topic_exists("codeatlas-events")
    print(f"Topic exists: {exists}")
    
    # List all topics
    topics = KafkaAdmin.list_topics()
    print(f"Available topics: {topics}")


def example_producer():
    """Example: Produce messages to Kafka"""
    print("\n=== Producer Example ===")
    
    # Send a single message
    message = {
        "event_type": "code_analysis",
        "project_id": "project-123",
        "timestamp": "2026-02-04T18:15:30",
        "data": {
            "files_analyzed": 42,
            "issues_found": 5
        }
    }
    
    ProducerHelper.send_message(
        topic="codeatlas-events",
        message=message,
        key="project-123"
    )
    
    # Send a batch of messages
    messages = [
        {"event_type": "file_created", "file_name": "test1.py"},
        {"event_type": "file_updated", "file_name": "test2.py"},
        {"event_type": "file_deleted", "file_name": "test3.py"},
    ]
    
    successful, failed = ProducerHelper.send_batch(
        topic="codeatlas-events",
        messages=messages,
        key_field="file_name"
    )
    print(f"Batch send: {successful} successful, {failed} failed")
    
    # Flush pending messages
    ProducerHelper.flush()


def example_consumer():
    """Example: Consume messages from Kafka"""
    print("\n=== Consumer Example ===")
    
    # Define a message handler
    def handle_message(message):
        print(f"Processing message: {message}")
        # Add your processing logic here
    
    # Consume messages (this will run indefinitely)
    # Uncomment to test:
    # ConsumerHelper.consume_messages(
    #     topics=["codeatlas-events"],
    #     message_handler=handle_message,
    #     max_messages=10  # Limit for demo purposes
    # )


def example_consumer_with_context():
    """Example: Consume messages with full context"""
    print("\n=== Consumer with Context Example ===")
    
    # Define a context-aware handler
    def handle_with_context(context):
        print(f"Topic: {context['topic']}")
        print(f"Partition: {context['partition']}")
        print(f"Offset: {context['offset']}")
        print(f"Message: {context['value']}")
        print("-" * 50)
    
    # Consume with context (this will run indefinitely)
    # Uncomment to test:
    # ConsumerHelper.consume_with_context(
    #     topics=["codeatlas-events"],
    #     message_handler=handle_with_context
    # )


def example_peek_messages():
    """Example: Peek at messages without consuming them"""
    print("\n=== Peek Messages Example ===")
    
    # Peek at the first 5 messages
    messages = ConsumerHelper.peek_messages(
        topics=["codeatlas-events"],
        count=5
    )
    
    print(f"Peeked {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"{i}. {msg}")


def cleanup():
    """Example: Clean up connections"""
    print("\n=== Cleanup ===")
    
    # Close producer and admin client
    KafkaConnection.close_producer()
    KafkaConnection.close_admin_client()
    print("Connections closed")


if __name__ == "__main__":
    """
    Run examples
    
    Note: Make sure Kafka is running before executing these examples.
    You can start Kafka using Docker:
    
    docker run -d --name kafka -p 9092:9092 \
        -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
        apache/kafka:latest
    """
    
    try:
        # Run admin operations
        example_admin_operations()
        
        # Run producer example
        example_producer()
        
        # Peek at messages
        # example_peek_messages()
        
        # Run consumer examples (commented out to avoid blocking)
        # example_consumer()
        # example_consumer_with_context()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always cleanup
        cleanup()
