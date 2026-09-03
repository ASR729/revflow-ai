import sys
sys.path.insert(0, '.')

from revflow.classifier.rules import classify_by_rules
from revflow.ingestion.normaliser import normalise_event
from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT * FROM events WHERE run_id = ? AND event_type = ?', ('RUN-PHASE4-FINAL', 'b2b_receivable')).fetchall()
    for e in events[:10]:
        event = normalise_event(dict(e), e['run_id'], e['event_id'])
        cause = classify_by_rules(event)
        decline_msg = e['decline_message'][:30] if e['decline_message'] else None
        print(e['event_id'] + ': true=' + e['true_cause'] + ' / decline_code=' + str(e['decline_code']) + ' / decline_msg=' + str(decline_msg) + ' / due=' + str(e['invoice_due_date']) + ' / ladder=' + e['ladder_step'] + ' -> cause=' + (cause.value if cause else 'None'))