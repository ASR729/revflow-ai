import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

run_id = 'RUN-20260904T110538'
with get_connection() as conn:
    run = conn.execute('SELECT * FROM batch_runs WHERE run_id = ?', (run_id,)).fetchone()
    if run:
        print('Run found:')
        for key in run.keys():
            print('  ' + key + ': ' + str(run[key]))
    else:
        print('Run not found')
    
    # Check events
    events = conn.execute('SELECT COUNT(*) as cnt FROM events WHERE run_id = ?', (run_id,)).fetchone()
    print('Events count: ' + str(events['cnt']))
    
    # Check audit_log
    audit = conn.execute('SELECT COUNT(*) as cnt FROM audit_log WHERE run_id = ?', (run_id,)).fetchone()
    print('Audit log count: ' + str(audit['cnt']))
    
    # Check escalations
    esc = conn.execute('''
        SELECT COUNT(*) as cnt FROM escalations e
        JOIN audit_log al ON e.audit_log_id = al.id
        WHERE al.run_id = ?
    ''', (run_id,)).fetchone()
    print('Escalations: ' + str(esc['cnt']))
    
    # Check ptp_commitments
    ptp = conn.execute('SELECT COUNT(*) as cnt FROM ptp_commitments WHERE run_id = ?', (run_id,)).fetchone()
    print('PTP commitments: ' + str(ptp['cnt']))
    
    # Check simulated_actions via join
    sim = conn.execute('''
        SELECT COUNT(*) as cnt FROM simulated_actions sa
        JOIN audit_log al ON sa.audit_log_id = al.id
        WHERE al.run_id = ?
    ''', (run_id,)).fetchone()
    print('Simulated actions: ' + str(sim['cnt']))