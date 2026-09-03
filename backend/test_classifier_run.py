import sys
sys.path.insert(0, '.')

from revflow.classifier.rules import classify_by_rules
from revflow.ingestion.normaliser import normalise_event
from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT * FROM events WHERE run_id = ? LIMIT 10', ('RUN-20260901T120005',)).fetchall()
    for e in events:
        event = normalise_event(dict(e), e['run_id'], e['event_id'])
        cause = classify_by_rules(event)
        decline_msg = e['decline_message'][:30] if e['decline_message'] else None
        print(f'{e["event_id"]}: {e["event_type"]} / true={e["true_cause"]} / decline_code={e["decline_code"]} / decline_msg={decline_msg} -> cause={cause.value if cause else None}')