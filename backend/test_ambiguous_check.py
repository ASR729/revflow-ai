import sys
sys.path.insert(0, '.')

from revflow.classifier.rules import classify_by_rules
from revflow.ingestion.normaliser import normalise_event
from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT * FROM events WHERE run_id = ? AND decline_message IS NOT NULL', ('RUN-PHASE4-FINAL',)).fetchall()
    print('Total with decline_message:', len(events))
    rule_count = 0
    llm_count = 0
    for e in events:
        event = normalise_event(dict(e), e['run_id'], e['event_id'])
        cause = classify_by_rules(event)
        if cause is not None:
            rule_count += 1
            print('RULE (should be LLM): ' + e['event_id'] + ' true=' + e['true_cause'] + ' decline_code=' + str(e['decline_code']) + ' msg=' + (e['decline_message'][:30] if e['decline_message'] else 'None'))
        else:
            llm_count += 1
    print('Rule (should be 0):', rule_count)
    print('LLM (should be 36):', llm_count)