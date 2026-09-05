import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json

base_url = "http://127.0.0.1:8000"

# Test POST /run-batch with detailed error
resp = requests.post(f"{base_url}/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")
print(f"Response: {resp.text}")

if resp.status_code == 202:
    data = resp.json()
    run_id = data.get('run_id')
    print(f"Run ID: {run_id}")
    
    # Check if it's running
    import time
    time.sleep(2)
    resp2 = requests.get(f"{base_url}/runs", timeout=10)
    if resp2.status_code == 200:
        for r in resp2.json().get('runs', []):
            if r['run_id'] == run_id:
                print(f"Run status: {r['status']}")
                break
else:
    print(f"Error: {resp.status_code} - {resp.text}")
    # Try to get more details
    try:
        error_detail = resp.json()
        print(f"Error detail: {json.dumps(error_detail, indent=2)}")
    except:
        pass