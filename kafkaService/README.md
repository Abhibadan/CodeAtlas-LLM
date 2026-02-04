# Kafka Service Configuration

This directory contains the Kafka integration for CodeAtlas LLM.

## Overview

The Kafka service provides a clean, Pythonic interface for working with Apache Kafka, including:
- **Connection Management**: Singleton pattern for efficient connection reuse
- **Admin Utilities**: Topic creation, deletion, and management
- **Producer Helpers**: Send individual or batch messages
- **Consumer Helpers**: Consume messages with various patterns

## Prerequisites

1. **Kafka Server**: Ensure Kafka is running and accessible
2. **Dependencies**: Install kafka-python via poetry

```bash
poetry install
```

## Configuration

Configure Kafka in your `.env` file:

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=codeatlas-consumer-group
```

For multiple brokers, separate with commas:
```bash
KAFKA_BOOTSTRAP_SERVERS=broker1:9092,broker2:9092,broker3:9092
```

## Quick Start

### 1. Admin Operations

```python
from kafkaService import KafkaAdmin

# Create a topic
KafkaAdmin.create_topic(
    topic_name="my-topic",
    num_partitions=3,
    replication_factor=1
)

# Check if topic exists
exists = KafkaAdmin.topic_exists("my-topic")

# List all topics
topics = KafkaAdmin.list_topics()

# Delete a topic
KafkaAdmin.delete_topic("my-topic")
```

### 2. Producing Messages

```python
from kafkaService import ProducerHelper

# Send a single message
ProducerHelper.send_message(
    topic="my-topic",
    message={"event": "user_login", "user_id": 123},
    key="user-123"
)

# Send batch messages
messages = [
    {"event": "event1", "data": "..."},
    {"event": "event2", "data": "..."},
]

successful, failed = ProducerHelper.send_batch(
    topic="my-topic",
    messages=messages,
    key_field="event"  # Use 'event' field as message key
)
```

### 3. Consuming Messages

```python
from kafkaService import ConsumerHelper

# Simple consumer
def handle_message(message):
    print(f"Received: {message}")

ConsumerHelper.consume_messages(
    topics=["my-topic"],
    message_handler=handle_message,
    max_messages=100  # Optional limit
)

# Consumer with context (includes metadata)
def handle_with_context(context):
    print(f"Topic: {context['topic']}")
    print(f"Offset: {context['offset']}")
    print(f"Value: {context['value']}")

ConsumerHelper.consume_with_context(
    topics=["my-topic"],
    message_handler=handle_with_context
)

# Peek at messages without committing
messages = ConsumerHelper.peek_messages(
    topics=["my-topic"],
    count=10
)
```

### 4. Connection Management

```python
from kafkaService import KafkaConnection

# Connections are created automatically and reused
producer = KafkaConnection.get_producer()
admin_client = KafkaConnection.get_admin_client()
consumer = KafkaConnection.get_consumer(["my-topic"])

# Cleanup when done
KafkaConnection.close_producer()
KafkaConnection.close_admin_client()
```

## Architecture

```
kafkaService/
├── __init__.py           # Main exports
├── connection.py         # Connection management (singleton)
├── admin.py              # Topic administration
├── helpers/
│   ├── __init__.py
│   ├── createProducer.py # Producer utilities
│   └── createComsumer.py # Consumer utilities
├── example_usage.py      # Usage examples
└── README.md             # This file
```

## Features

### Producer Features
- ✅ JSON serialization
- ✅ Message keys for partitioning
- ✅ Batch sending
- ✅ Acknowledgment control
- ✅ Retry logic
- ✅ Flush support

### Consumer Features
- ✅ JSON deserialization
- ✅ Consumer groups
- ✅ Offset management
- ✅ Auto-commit
- ✅ Context-aware consumption
- ✅ Peek without committing

### Admin Features
- ✅ Topic creation with partitions
- ✅ Topic deletion
- ✅ List topics
- ✅ Topic existence check

## Running Kafka with Docker

```bash
# Start Kafka
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  apache/kafka:latest

# Stop Kafka
docker stop kafka
docker rm kafka
```

Or using docker-compose (if available in your project):

```bash
docker-compose up -d kafka
```

## Example Usage

See `example_usage.py` for comprehensive examples:

```bash
python kafkaService/example_usage.py
```

## Error Handling

All Kafka operations include proper error handling:

```python
from kafka.errors import KafkaError

try:
    ProducerHelper.send_message("my-topic", {"data": "test"})
except KafkaError as e:
    print(f"Kafka error: {e}")
```

## Best Practices

1. **Reuse connections**: The singleton pattern ensures connection reuse
2. **Use message keys**: For proper partitioning and ordering
3. **Batch when possible**: Better performance for multiple messages
4. **Handle errors**: Always catch and handle KafkaError
5. **Cleanup**: Close connections when shutting down
6. **Consumer groups**: Use for load balancing across consumers
7. **Monitoring**: Check logs for connection and processing issues

## Integration with CodeAtlas

This Kafka service can be used for:
- **Event streaming**: Code analysis events, file changes
- **Job queuing**: Distribute analysis tasks across workers
- **Real-time updates**: Stream code metrics to dashboards
- **Audit logging**: Track all code operations
- **Microservices communication**: Event-driven architecture

## Troubleshooting

### Connection Issues
- Verify Kafka is running: `docker ps | grep kafka`
- Check broker address in `.env`
- Ensure firewall allows port 9092

### Topic Not Found
- Create topic manually: `KafkaAdmin.create_topic("topic-name")`
- Enable auto-topic creation in Kafka config

### Consumer Not Receiving Messages
- Check consumer group ID
- Verify topic has messages
- Check offset reset strategy

## License

Part of CodeAtlas LLM project.
