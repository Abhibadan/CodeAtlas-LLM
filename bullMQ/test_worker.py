"""
Simple Worker Test - Single Worker
"""

from bullMQ import WorkerLoader, WorkerRegistry
import time
import signal
import sys
import asyncio
import os
from contextlib import contextmanager


@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr to hide BullMQ library errors"""
    stderr_fd = sys.stderr.fileno()
    old_stderr = os.dup(stderr_fd)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, stderr_fd)
        yield
    finally:
        os.dup2(old_stderr, stderr_fd)
        os.close(devnull)
        os.close(old_stderr)


async def process_email_job(job, job_token):
    """Process email jobs"""
    print("\n" + "="*70)
    print("📧 WORKER RECEIVED JOB")
    print("="*70)
    print(f"Job Name: {job.name}")
    print(f"Job ID: {job.id}")
    print(f"Job Token: {job_token}")
    print("\n📦 DATA RECEIVED:")
    print(f"   to: {job.data.get('to')}")
    print(f"   subject: {job.data.get('subject')}")
    print(f"   body: {job.data.get('body')}")
    print("\n✓ Job processed successfully!")
    print("="*70 + "\n")
    
    # Return a success result
    return {"status": "sent", "timestamp": time.time()}


async def test_worker():
    """Quick test of worker setup"""
    print("=== Testing Worker Setup ===\n")
    
    worker = WorkerLoader(
        worker_name=WorkerRegistry.EMAIL_WORKER,
        process_job=process_email_job
    )
    
    print("✓ Worker created successfully")
    print("\nTo run in daemon mode: python test_worker.py --daemon\n")
    
    # Cleanup
    await worker.close_worker()
    print("✓ Worker closed\n")


async def run_daemon_async():
    """Run worker in daemon mode with async event loop"""
    print("\n" + "="*70)
    print("STARTING EMAIL WORKER DAEMON")
    print("="*70)
    # Explicitly use .value to pass a string
    worker_name_str = WorkerRegistry.EMAIL_WORKER.value
    print(f"Worker Queue: {worker_name_str}")
    print("Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    print("✓ Worker initialized and waiting for jobs...\n")
    
    # Create worker once and let it run continuously
    worker_loader = WorkerLoader(
        worker_name=worker_name_str,
        process_job=process_email_job
    )
    worker = worker_loader.get_worker()
    
    try:
        # worker.run() is designed to run continuously and process jobs as they arrive
        # Suppress stderr to hide BullMQ library's internal ValueError traceback
        with suppress_stderr():
            await worker.run()
    except KeyboardInterrupt:
        print("\n✓ Received stop signal...")
    except ValueError as e:
        # Suppress the "Set of Tasks/Futures is empty" error from BullMQ library
        # This is a known issue when the worker starts with no jobs
        if "Set of Tasks/Futures is empty" not in str(e):
            print(f"\n❌ Worker error: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Worker error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await worker_loader.close_worker()
        print("\n✓ Worker daemon stopped")


def run_daemon():
    """Entry point for daemon mode"""
    try:
        asyncio.run(run_daemon_async())
    except KeyboardInterrupt:
        print("\n✓ Worker stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test BullMQ Worker")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run worker in daemon mode"
    )
    
    args = parser.parse_args()
    
    try:
        if args.daemon:
            run_daemon()
        else:
            asyncio.run(test_worker())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
