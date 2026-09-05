import asyncio
import subprocess
import sys
import time
import requests
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

# Start server
server_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "revflow.main:app", 
    "--host", "127.0.0.1", "--port", "8000", "--log-level", "error"
], cwd=os.path.dirname(__file__))

# Wait for server to start
time.sleep(4)

base_url = "http://127.0.0.1:8000"

try:
    # Test all 10 endpoints
    print("Testing all 10 endpoints:")
    
    # 1. GET /health
    resp = requests.get(f"{base_url}/health", timeout=10)
    print(f"  GET /health: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 2. GET /runs
    resp = requests.get(f"{base_url}/runs", timeout=10)
    print(f"  GET /runs: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 3. GET /metrics
    resp = requests.get(f"{base_url}/metrics", timeout=10)
    print(f"  GET /metrics: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 4. GET /classifier-metrics
    resp = requests.get(f"{base_url}/classifier-metrics", timeout=10)
    print(f"  GET /classifier-metrics: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 5. GET /audit-log
    resp = requests.get(f"{base_url}/audit-log", timeout=10)
    print(f"  GET /audit-log: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 6. GET /exceptions
    resp = requests.get(f"{base_url}/exceptions", timeout=10)
    print(f"  GET /exceptions: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 7. GET /events/{event_id} - use a valid event ID
    # First get a valid event ID
    resp = requests.get(f"{base_url}/audit-log", timeout=10)
    if resp.status_code == 200:
        audit_data = resp.json()
        if audit_data.get('rows'):
            event_id = audit_data['rows'][0]['event_id']
            resp = requests.get(f"{base_url}/events/{event_id}", timeout=10)
            print(f"  GET /events/{{event_id}}: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
        else:
            print(f"  GET /events/{{event_id}}: SKIP (no events)")
    else:
        print(f"  GET /events/{{event_id}}: SKIP (audit-log failed)")
    
    # 8. GET /config
    resp = requests.get(f"{base_url}/config", timeout=10)
    print(f"  GET /config: {'PASS' if resp.status_code == 200 else f'FAIL ({resp.status_code})'}")
    
    # 9. POST /run-batch
    resp = requests.post(f"{base_url}/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=10)
    print(f"  POST /run-batch: {'PASS' if resp.status_code == 202 else f'FAIL ({resp.status_code})'}")
    
    # 10. POST /webhook
    resp = requests.post(f"{base_url}/webhook", json={"event": "test", "payload": {}}, timeout=10)
    print(f"  POST /webhook: {'PASS' if resp.status_code in (200, 202) else f'FAIL ({resp.status_code})'}")
    
    # Test concurrent call rejection (409)
    print("\nTesting concurrent call rejection:")
    # First call
    resp1 = requests.post(f"{base_url}/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=10)
    print(f"  First call: {resp1.status_code}")
    time.sleep(2)  # Give background task time to start and mark batch as running
    # Second call - should be 409
    resp2 = requests.post(f"{base_url}/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=10)
    print(f"  Second call (should be 409): {resp2.status_code}")
    if resp2.status_code == 409:
        print("  Concurrent rejection: PASS")
    else:
        print(f"  Concurrent rejection: FAIL (got {resp2.status_code})")

finally:
    # The server runs in background, we can't easily kill it from here
    pass