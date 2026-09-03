import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

run_id = "RUN-DEBUG-CHECK-2"
with get_connection() as conn:
    # Check ladder steps in audit log
    steps = conn.execute('SELECT DISTINCT ladder_step FROM audit_log WHERE run_id = ? AND event_type = ? AND ladder_step != "none" ORDER BY ladder_step', 
                         (run_id, 'b2b_receivable')).fetchall()
    print('Ladder steps in audit_log:', [s['ladder_step'] for s in steps])
    
    # Check actions for B2B
    actions = conn.execute('SELECT action, ladder_step, COUNT(*) as cnt FROM audit_log WHERE run_id = ? AND event_type = ? GROUP BY action, ladder_step', 
                           (run_id, 'b2b_receivable')).fetchall()
    for a in actions:
        print(f'  action={a["action"]}, ladder_step={a["ladder_step"]}, count={a["cnt"]}')