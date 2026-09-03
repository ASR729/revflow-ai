import sys
sys.path.insert(0, '.')

from revflow.classifier.rules import classify_by_rules
from revflow.ingestion.normaliser import normalise_event
from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT * FROM events WHERE run_id = ?', ('RUN-PHASE4-FINAL',)).fetchall()
    rule_count = 0
    llm_count = 0
    unclassified = 0
    for e in events:
        event = normalise_event(dict(e), e['run_id'], e['event_id'])
        cause = classify_by_rules(event)
        if cause is not None:
            rule_count += 1
        else:
            # Check if it would go to LLM (has decline_message)
            if e['decline_message'] and e['decline_message'].strip():
                llm_count += 1
            else:
                unclassified += 1
    print('Rule:', rule_count)
    print('LLM (has decline_message):', llm_count)
    print('Unclassified (no decline_message):', unclassified)
    print('Total:', rule_count + llm_count + unclassified)