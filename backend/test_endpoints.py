import httpx
from revflow.db.connection import get_connection

with get_connection() as conn:
    runs = conn.execute("SELECT run_id FROM batch_runs WHERE status = ? ORDER BY completed_at DESC", ("completed",)).fetchall()
    run_id = runs[0]["run_id"] if runs else None
    events = conn.execute("SELECT event_id FROM events WHERE run_id = ? LIMIT 1", (run_id,)).fetchall()
    event_id = events[0]["event_id"] if events else None

print("Testing all 10 endpoints with run_id:", run_id, "event_id:", event_id)

endpoints = [
    ("GET", "/health", None, 200),
    ("GET", "/config", None, 200),
    ("POST", "/run-batch", {"use_llm": False, "regenerate_dataset": False}, 202),
    ("GET", "/runs", None, 200),
    ("GET", "/metrics", {"run_id": run_id}, 200),
    ("GET", "/classifier-metrics", {"run_id": run_id}, 200),
    ("GET", "/audit-log", {"run_id": run_id}, 200),
    ("GET", "/exceptions", {"run_id": run_id}, 200),
    ("GET", "/events/" + event_id, None, 200),
]

for method, path, body, expected in endpoints:
    if method == "GET":
        r = httpx.get("http://127.0.0.1:8001" + path, params=body if body else None)
    else:
        r = httpx.post("http://127.0.0.1:8001" + path, json=body)
    status = "PASS" if r.status_code == expected else "FAIL"
    print(method + " " + path + ": " + status + " (got " + str(r.status_code) + ", expected " + str(expected) + ")")

# Test webhook
r = httpx.post("http://127.0.0.1:8001/webhook", json={"event": "payment.failed", "payload": {"amount": 1000, "customer_id": "CUST-9999"}})
print("POST /webhook: " + ("PASS" if r.status_code == 202 else "FAIL") + " (got " + str(r.status_code) + ")")

# Test invalid enum validation
r = httpx.get("http://127.0.0.1:8001/audit-log", params={"event_type": "invalid_type"})
print("GET /audit-log?event_type=invalid_type: " + ("PASS" if r.status_code == 422 else "FAIL") + " (got " + str(r.status_code) + ")")