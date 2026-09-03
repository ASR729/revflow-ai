import sys
sys.path.insert(0, '.')

from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT true_cause, dispute_raised FROM events WHERE run_id = ? AND event_type = ?', ('RUN-PHASE4-FINAL3', 'b2b_receivable')).fetchall()
    print('Total B2B events:', len(events))
    for e in events:
        print('true_cause=' + e['true_cause'] + ', dispute_raised=' + str(e['dispute_raised']))