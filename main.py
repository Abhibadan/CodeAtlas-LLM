import subprocess
import signal
import sys
from kafkaService import KafkaConnection,TopicRegistry
import logging
logger = logging.getLogger(__name__)
# Global list to track subprocesses
processes = []

def cleanup_processes(signum=None, frame=None):
    """Terminate all child processes"""
    logger.info("Shutting down Kafka connections...")
    KafkaConnection.close_producer()
    KafkaConnection.close_admin_client()
    logger.info("Kafka connections closed.")
    logger.info("Shutting down subprocesses...")
    for proc in processes:
        if proc.poll() is None:  # Check if process is still running
            logger.info(f"Terminating process {proc.pid}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                logger.info(f"Force killing process {proc.pid}...")
                proc.kill()  # Force kill if it doesn't terminate
    logger.info("All subprocesses terminated.")
    sys.exit(0)

def main():
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_processes)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, cleanup_processes)  # Handle terminal close
    
    
    # Start subprocesses and track them
    logger.info("Starting server.py...")
    processes.append(subprocess.Popen(["python", "server.py"]))
    
    logger.info("Starting vectorizer.py...")
    processes.append(subprocess.Popen(["python", "vectorizer.py"]))
    
    logger.info("Creating Kafka topics...")
    exists = KafkaAdmin.topic_exists(TopicRegistry.CODEATLAS_LLM_EVENTS.value)
    if not exists:
        KafkaConnection.create_topics()
        KafkaAdmin.create_topic(
            topic_name=TopicRegistry.CODEATLAS_LLM_EVENTS.value,
            num_partitions=4,
            replication_factor=1
        )
    
    logger.info("All subprocesses started. Press Ctrl+C to stop.")
    
    # Keep the main process running and wait for processes
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup_processes()

if __name__ == "__main__":
    main()
