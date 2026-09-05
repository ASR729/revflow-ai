import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

run_id = 'RUN-20260904T115822'
with get_connection() as conn:
    run = conn.execute('SELECT * FROM batch_runs WHERE run_id = ?', (run_id,)).fetchone()
    if run:
        print('Run found:')
        for key in run.keys():
            print('  ' + key + ': ' + str(run[key]))
    else:
        print('Run not found')
    
    events = conn.execute('SELECT COUNT(*) as cnt FROM events WHERE run_id = ?', (run_id,)).fetchone()
    print('Events count: ' + str(events['cnt']))
    
    audit = conn.execute('SELECT COUNT(*) as cnt FROM audit_log WHERE run_id = ?', (run_id,)).fetchone()
    print('Audit log count: ' + str(audit['cnt']))
    
    actions = conn.execute('SELECT action, COUNT(*) as cnt FROM audit_log WHERE run_id = ? GROUP BY action', (run_id,)).fetchall()
    for row in actions:
        print('  ' + row['action'] + ': ' + str(row['cnt']))