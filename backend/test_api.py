import asyncio
import subprocess
import sys
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_endpoints():
    # Start server
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "revflow.main:app", 
        "--host", "127.0.0.1", "--port", "8000", "--log-level", "error"
    ], cwd=Path(__file__).parent)
    
    # Wait for server to start
    time.sleep(3)
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Test all 10 endpoints
        endpoints = [
            ("GET", "/health"),
            ("GET", "/runs"),
            ("GET", "/metrics?run_id=RUN-TEST7-PHASE7-1"),
            ("GET", "/classifier-metrics?run_id=RUN-TEST7-PHASE7-1"),
            ("GET", "/audit-log?run_id=RUN-TEST7-PHASE7-1"),
            ("GET", "/exceptions?run_id=RUN-TEST7-PHASE7-1"),
            ("GET", "/events/EVT-0901120019-0001"),
            ("GET", "/config"),
            ("POST", "/run-batch", {"use_llm": False, "regenerate_dataset": False}),
            ("POST", "/webhook", {"event": "test", "payload": {}}),
        ]
        
        print("Testing all 10 endpoints:")
        for method, endpoint, *data in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                if method == "GET":
                    resp = requests.get(url, timeout=10)
                elif method == "POST":
                    json_data = data[0] if data else {}
                    resp = requests.post(url, json=json_data, timeout=10)
                
                status = "PASS" if resp.status_code in (200, 202) else f"FAIL ({resp.status_code})"
                print(f"  {method} {endpoint}: {status}")
            except Exception as e:
                print(f"  {method} {endpoint}: FAIL ({e})")
        
        # Test concurrent call rejection (409)
        print("\nTesting concurrent call rejection:")
        resp1 = requests.post(f"{base_url}/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=10)
        time.sleep(0.5)
        resp2 = requests.post(f"{base_url}/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=10)
        print(f"  First call: {resp1.status_code}")
        print(f"  Second call (should be 409): {resp2.status_code}")
        if resp2.status_code == 409:
            print("  Concurrent rejection: PASS")
        else:
            print("  Concurrent rejection: FAIL")
        
    finally:
        server_process.terminate()
        server_process.wait()

# Run server in background
import subprocess
import sys
import os

server_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "revflow.main:app", 
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "error"
], cwd=os.path.dirname(__file__))

time.sleep(3)

asyncio.run(test_endpoints())