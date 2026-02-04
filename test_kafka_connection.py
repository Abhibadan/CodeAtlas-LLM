#!/usr/bin/env python3
"""
Quick Kafka connection test script
Tests basic connectivity and metadata retrieval from Kafka broker
"""
import sys
from kafka import KafkaAdminClient
from kafka.errors import KafkaError

BROKER = "localhost:19092"

print(f"Testing Kafka connection to {BROKER}...")
print("-" * 60)

try:
    # Try to create admin client with a shorter timeout
    print("Creating admin client...")
    admin = KafkaAdminClient(
        bootstrap_servers=[BROKER],
        client_id='test-client',
        request_timeout_ms=10000,  # 10 seconds
        api_version_auto_timeout_ms=5000  # 5 seconds for version detection
    )
    
    print("✓ Successfully connected to Kafka broker!")
    
    # Try to list topics
    print("\nListing topics...")
    topics = admin.list_topics()
    print(f"✓ Found {len(topics)} topics:")
    for topic in sorted(topics):
        if not topic.startswith('__'):  # Skip internal topics
            print(f"  - {topic}")
    
    admin.close()
    print("\n✓ Connection test successful!")
    sys.exit(0)
    
except KafkaError as e:
    print(f"\n✗ Kafka error: {e}")
    print(f"\nError type: {type(e).__name__}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    print(f"\nError type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
