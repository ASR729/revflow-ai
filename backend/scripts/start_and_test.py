import subprocess
import sys
import os
import time
import requests

backend_dir = os.path.dirname(os.path.dirname(__file__))

# Start server and capture stderr
server_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "revflow.main:app", 
    "--host", "127.0.0.1", "--port", "8001", "--log-level", "debug"
], cwd=backend_dir, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(4)

# Check if server is running
import subprocess as sp
result = sp.run(['netstat', '-ano'], capture_output=True, text=True)
print("Netstat output:")
print(result.stdout)

# Test the API
print("\nTesting POST /run-batch...")
try:
    resp = requests.post("http://127.0.0.1:8001/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")

# Read stdout/stderr
try:
    stdout_output = server_process.stdout.read()
    stderr_output = server_process.stderr.read()
    print("\n=== SERVER STDOUT ===")
    print(stdout_output)
    print("\n=== SERVER STDERR ===")
    print(stderr_output)
except Exception as e:
    print(f"Error reading output: {e}")

server_process.terminate()
server_process.wait()
print("Done")