import requests
import json

base_url = "http://127.0.0.1:8001"

print("=== STEP 2: READ-ONLY ENDPOINTS ===")

# 1. GET /health
resp = requests.get(f"{base_url}/health", timeout=10)
print("1. GET /health:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
print("  Response:", resp.json())

# 2. GET /runs
resp = requests.get(f"{base_url}/runs", timeout=10)
print("\n2. GET /runs:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
if resp.status_code == 200:
    runs = resp.json().get('runs', [])
    print("  Runs count:", len(runs))
    if runs:
        print("  Latest run:", runs[0]['run_id'], runs[0]['status'])

# 3. GET /metrics
resp = requests.get(f"{base_url}/metrics", timeout=10)
print("\n3. GET /metrics:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
if resp.status_code == 200:
    m = resp.json()
    print("  event_count:", m.get('event_count'))
    print("  recovery_rate:", m.get('rates', {}).get('recovery_rate_realised'))

# 4. GET /classifier-metrics
resp = requests.get(f"{base_url}/classifier-metrics", timeout=10)
print("\n4. GET /classifier-metrics:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
if resp.status_code == 200:
    cm = resp.json()
    print("  run_id:", cm.get('run_id'))
    print("  accuracy:", cm.get('overall', {}).get('accuracy'))

# 5. GET /audit-log?run_id=RUN-20260904T110538
resp = requests.get(f"{base_url}/audit-log", params={"run_id": "RUN-20260904T110538"}, timeout=10)
print("\n5. GET /audit-log?run_id=RUN-20260904T110538:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
if resp.status_code == 200:
    al = resp.json()
    print("  Total rows:", al.get('total'))
    print("  Returned rows:", len(al.get('rows', [])))

# 6. GET /exceptions
resp = requests.get(f"{base_url}/exceptions", timeout=10)
print("\n6. GET /exceptions:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
if resp.status_code == 200:
    exc = resp.json()
    print("  withheld_count:", len(exc.get('withheld_by_policy', [])))
    print("  needs_human_count:", len(exc.get('needs_a_human', [])))

# 7. GET /events/{real_event_id}
# First get a real event_id from the run
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from revflow.db.connection import get_connection

with get_connection() as conn:
    event_row = conn.execute(
        'SELECT event_id FROM events WHERE run_id = ? LIMIT 1', 
        ('RUN-20260904T110538',)
    ).fetchone()

if event_row:
    event_id = event_row['event_id']
    resp = requests.get(f"{base_url}/events/{event_id}", timeout=10)
    print("\n7. GET /events/{event_id} (using real ID: " + event_id + "):")
    print("  Status:", resp.status_code)
    print("  Valid:", resp.status_code == 200)
    if resp.status_code == 200:
        event_data = resp.json()
        print("  Event ID:", event_data.get('event', {}).get('event_id'))
        print("  Timeline length:", len(event_data.get('timeline', [])))
else:
    print("\n7. GET /events/{event_id}: SKIPPED - no event found")

# 8. GET /config
resp = requests.get(f"{base_url}/config", timeout=10)
print("\n8. GET /config:")
print("  Status:", resp.status_code)
print("  Valid:", resp.status_code == 200)
if resp.status_code == 200:
    cfg = resp.json()
    print("  MAX_RETRIES:", cfg.get('MAX_RETRIES'))
    print("  LLM_CALL_BUDGET_PER_RUN:", cfg.get('LLM_CALL_BUDGET_PER_RUN'))