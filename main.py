import subprocess
import signal
import sys

# Global list to track subprocesses
processes = []

def cleanup_processes(signum=None, frame=None):
    """Terminate all child processes"""
    print("\nShutting down subprocesses...")
    for proc in processes:
        if proc.poll() is None:  # Check if process is still running
            print(f"Terminating process {proc.pid}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                print(f"Force killing process {proc.pid}...")
                proc.kill()  # Force kill if it doesn't terminate
    print("All subprocesses terminated.")
    sys.exit(0)

def main():
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_processes)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, cleanup_processes)  # Handle terminal close
    
    # Start subprocesses and track them
    print("Starting server.py...")
    processes.append(subprocess.Popen(["python", "server.py"]))
    
    print("Starting vectorizer.py...")
    processes.append(subprocess.Popen(["python", "vectorizer.py"]))
    
    print("All subprocesses started. Press Ctrl+C to stop.")
    
    # Keep the main process running and wait for processes
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup_processes()

if __name__ == "__main__":
    main()
