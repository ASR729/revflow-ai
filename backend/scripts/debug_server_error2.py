import sys
import os
import json
import subprocess
import time
import requests
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

backend_dir = os.path.dirname(os.path.dirname(__file__))

# Start server and capture stderr
server_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "revflow.main:app", 
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "debug"
], cwd=backend_dir, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

# Read stderr in a separate thread
stderr_queue = queue.Queue()

def read_stderr():
    for line in iter(server_process.stderr.readline, b''):
        stderr_queue.put(line.decode('utf-8', errors='replace'))

stderr_thread = threading.Thread(target=read_stderr, daemon=True)
stderr_thread.start()

# Wait for server to start
time.sleep(4)

base_url = "http://127.0.0.1:8000"

try:
    # Test POST /run-batch
    print("Testing POST /run-batch...")
    resp = requests.post(f"http://127.0.0.1:8000/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Wait a bit for background task to log errors
    time.sleep(3)
    
    # Get stderr output
    stderr_output = ""
    while not stderr_queue.empty():
        stderr_output += stderr_queue.get()
    
    print("\n=== SERVER STDERR ===")
    print(stderr_output[-10000:])  # Last 10000 chars
    
finally:
    server_process.terminate()
    server_process.wait()