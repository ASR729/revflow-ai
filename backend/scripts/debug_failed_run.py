import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

run_id = "RUN-20260904T051203"
with get_connection() as conn:
    # Check the run
    run = conn.execute('SELECT * FROM batch_runs WHERE run_id = ?', (run_id,)).fetchone()
    if run:
        print(f"Run: {dict(run)}")
    
    # Check audit log for this run
    audit = conn.execute('SELECT * FROM audit_log WHERE run_id = ? ORDER BY created_at DESC LIMIT 10', (run_id,)).fetchall()
    for a in audit:
        print(f"  Audit: action={a['action']}, outcome={a['outcome']}, rule_fired={a['rule_fired']}, rationale={a['rationale'][:80] if a['rationale'] else None}...")
    
    # Check events
    events = conn.execute('SELECT * FROM events WHERE run_id = ? LIMIT 5', (run_id,)).fetchall()
    for e in events:
        print(f"  Event: {e['event_id']}, type={e['event_type']}, cause={e['true_cause']}, ladder={e['ladder_step']}")