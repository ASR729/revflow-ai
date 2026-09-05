import subprocess
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(__file__))

# Start server and capture stderr
server_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "revflow.main:app", 
    "--host", "127.0.0.1", "--port", "8001", "--log-level", "debug"
], cwd=backend_dir, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

import time
time.sleep(3)

print("Checking if server is running...")
netstat_check = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
print(netstat_check.stdout)

# Test the API
import requests
try:
    resp = requests.post("http://127.0.0.1:8001/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")

# Get stderr
stderr_output = server_process.stderr.read().decode('utf-8', errors='replace')
print("\n=== SERVER STDERR ===")
print(stderr_output)

server_process.terminate()