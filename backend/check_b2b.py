import sys
sys.path.insert(0, '.')

from revflow.db.connection import get_connection

with get_connection() as conn:
    runs = conn.execute('SELECT run_id FROM batch_runs ORDER BY started_at DESC').fetchall()
    for r in runs:
        print('Run:', r['run_id'])
        events = conn.execute('SELECT true_cause, dispute_raised FROM events WHERE run_id = ? AND event_type = ?', (r['run_id'], 'b2b_receivable')).fetchall()
        for e in events:
            print('  true_cause=' + e['true_cause'] + ', dispute_raised=' + str(e['dispute_raised']))