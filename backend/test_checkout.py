import sys
sys.path.insert(0, '.')

from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT event_type, decline_code, decline_message, true_cause, session_started_at FROM events WHERE run_id = ?', ('RUN-PHASE4-FINAL',)).fetchall()
    checkout_null = [e for e in events if e['event_type'] == 'checkout_dropoff' and e['decline_code'] is None]
    print('Checkout null decline_code:', len(checkout_null))
    with_msg = [e for e in checkout_null if e['decline_message']]
    print('With message:', len(with_msg))
    without_msg = [e for e in checkout_null if not e['decline_message']]
    print('Without message:', len(without_msg))
    for e in without_msg:
        print('  true=' + e['true_cause'] + ', session_started_at=' + str(e['session_started_at']))