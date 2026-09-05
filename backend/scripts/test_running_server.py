import requests
import json

base_url = "http://127.0.0.1:8000"

print("Testing POST /run-batch...")
resp = requests.post(f"http://127.0.0.1:8000/run-batch", json={"use_llm": False, "regenerate_dataset": False}, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

if resp.status_code == 202:
    data = resp.json()
    run_id = data.get('run_id')
    print(f"Run ID: {run_id}")
    
    import time
    time.sleep(5)
    resp2 = requests.get(f"{base_url}/runs", timeout=10)
    if resp2.status_code == 200:
        for r in resp2.json().get('runs', []):
            if r['run_id'] == run_id:
                print(f"Run status: {r['status']}")
                break

if resp.status_code != 202:
    print(f"Error: {resp.status_code} - {resp.text}")
    try:
        error_detail = resp.json()
        print(f"Error detail: {json.dumps(error_detail, indent=2)}")
    except:
        pass