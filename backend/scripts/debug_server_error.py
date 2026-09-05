import sys
import os
import json
import subprocess
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Start server and capture stderr
backend_dir = os.path.dirname(os.path.dirname(__file__))
server_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "revflow.main:app", 
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "debug"
], cwd=backend_dir, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

# Wait for server to start
time.sleep(4)

base_url = "http://127.0.0.1:8000"

try:
    # Test POST /run-batch
    print("Testing POST /run-batch...")
    resp = requests.post(f"http://127.0.0.1:8000/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Read server stderr
    stderr_output = server_process.stderr.read().decode('utf-8', errors='replace')
    print("\n=== SERVER STDERR ===")
    print(stderr_output[-5000:])  # Last 5000 chars
    
finally:
    server_process.terminate()
    server_process.wait()