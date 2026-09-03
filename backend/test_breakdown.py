import sys
sys.path.insert(0, '.')

from revflow.classifier.rules import classify_by_rules
from revflow.ingestion.normaliser import normalise_event
from revflow.db.connection import get_connection

with get_connection() as conn:
    events = conn.execute('SELECT * FROM events WHERE run_id = ?', ('RUN-PHASE4-FINAL',)).fetchall()
    rule_causes = {}
    llm_causes = {}
    unclassified_causes = {}
    for e in events:
        event = normalise_event(dict(e), e['run_id'], e['event_id'])
        cause = classify_by_rules(event)
        true_cause = e['true_cause']
        if e['decline_message'] and e['decline_message'].strip():
            src = 'llm'
        elif cause is not None:
            src = 'rule'
        else:
            src = 'unclassified'
        
        if src == 'rule':
            rule_causes[true_cause] = rule_causes.get(true_cause, 0) + 1
        elif src == 'llm':
            llm_causes[true_cause] = llm_causes.get(true_cause, 0) + 1
        else:
            unclassified_causes[true_cause] = unclassified_causes.get(true_cause, 0) + 1

    print('=== RULE ===')
    for c, n in sorted(rule_causes.items()):
        print(f'  {c}: {n}')
    print('Total rule:', sum(rule_causes.values()))
    
    print('\n=== LLM ===')
    for c, n in sorted(llm_causes.items()):
        print(f'  {c}: {n}')
    print('Total llm:', sum(llm_causes.values()))
    
    print('\n=== UNCLASSIFIED ===')
    for c, n in sorted(unclassified_causes.items()):
        print(f'  {c}: {n}')
    print('Total unclassified:', sum(unclassified_causes.values()))