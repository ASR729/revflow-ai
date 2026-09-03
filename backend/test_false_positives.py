import sys
sys.path.insert(0, '.')

from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('''
        SELECT e.event_id, e.true_cause, al.action, al.cause, al.cause_source
        FROM events e
        JOIN audit_log al ON e.event_id = al.event_id
        WHERE e.run_id = ? AND e.true_cause IN ("user_revoked", "invoice_disputed")
        AND al.action IN ("retry_now", "nudge")
    ''', ('RUN-PHASE4-FINAL2',)).fetchall()
    for e in events:
        print(e['event_id'] + ': true=' + e['true_cause'] + ', action=' + e['action'] + ', cause=' + e['cause'] + ', cause_source=' + e['cause_source'])