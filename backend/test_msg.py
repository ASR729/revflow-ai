import sys
sys.path.insert(0, '.')

from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT decline_message, true_cause, event_type FROM events WHERE run_id = ? AND decline_message IS NOT NULL', ('RUN-PHASE4-FINAL',)).fetchall()
    print('Total with decline_message:', len(events))
    for e in events:
        msg = e['decline_message'][:40] if e['decline_message'] else 'None'
        print('  ' + e['event_type'] + ': true=' + e['true_cause'] + ', msg=' + msg)