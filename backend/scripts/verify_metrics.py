import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import get_connection

run_id = 'RUN-20260904T110538'
with get_connection() as conn:
    print("=== STEP 3: METRICS + DB RECONCILIATION ===")
    print()
    
    # A. events = 300
    events = conn.execute('SELECT COUNT(*) as cnt FROM events WHERE run_id = ?', (run_id,)).fetchone()
    print('A. Events = 300:', 'PASS' if events['cnt'] == 300 else 'FAIL', '(' + str(events['cnt']) + ')')
    
    # B. audit_log = 300
    audit = conn.execute('SELECT COUNT(*) as cnt FROM audit_log WHERE run_id = ?', (run_id,)).fetchone()
    print('B. audit_log = 300:', 'PASS' if audit['cnt'] == 300 else 'FAIL', '(' + str(audit['cnt']) + ')')
    
    # C. action/audit population reconciles
    # action_breakdown sum = event_count
    action_counts = conn.execute(
        'SELECT action, COUNT(*) as cnt FROM audit_log WHERE run_id = ? GROUP BY action', (run_id,)
    ).fetchall()
    action_sum = sum(row['cnt'] for row in action_counts)
    print('C. action breakdown sum = event_count:', 'PASS' if action_sum == 300 else 'FAIL', '(' + str(action_sum) + ' = 300)')
    for row in action_counts:
        print('   ' + row['action'] + ': ' + str(row['cnt']))
    
    # outcome breakdown sum = event_count
    outcome_counts = conn.execute(
        'SELECT outcome, COUNT(*) as cnt FROM audit_log WHERE run_id = ? GROUP BY outcome', (run_id,)
    ).fetchall()
    outcome_sum = sum(row['cnt'] for row in outcome_counts)
    print('   outcome breakdown sum = event_count:', 'PASS' if outcome_sum == 300 else 'FAIL', '(' + str(outcome_sum) + ' = 300)')
    for row in outcome_counts:
        print('   ' + row['outcome'] + ': ' + str(row['cnt']))
    
    # D. escalations linked to audit rows
    esc = conn.execute('''
        SELECT COUNT(*) as cnt FROM escalations e
        JOIN audit_log al ON e.audit_log_id = al.id
        WHERE al.run_id = ?
    ''', (run_id,)).fetchone()
    print('D. Escalations linked to audit rows:', 'PASS' if esc['cnt'] == 36 else 'FAIL', '(' + str(esc['cnt']) + ')')
    
    # E. PTP commitments linked to events
    ptp = conn.execute('SELECT COUNT(*) as cnt FROM ptp_commitments WHERE run_id = ?', (run_id,)).fetchone()
    print('E. PTP commitments linked to events:', 'PASS' if ptp['cnt'] == 10 else 'FAIL', '(' + str(ptp['cnt']) + ')')
    
# F. summary_metrics corresponds to completed run
    import json
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # The file is at project_root/backend/data/summary_metrics.json
    project_root = os.path.dirname(os.path.dirname(script_dir))
    fpath = os.path.join(project_root, 'backend', 'backend', 'data', 'summary_metrics.json')
    fpath = os.path.normpath(fpath)
    print('DEBUG: looking for metrics at:', fpath)
    with open(fpath, 'r') as f:
        metrics = json.load(f)
    print('DEBUG: summary_metrics run_id:', repr(metrics.get('run_id')))
    print('DEBUG: expected run_id:', repr(run_id))
    
    # G. All §5.6 integrity fields are zero
    integrity = metrics.get('integrity', {})
    integrity_ok = True
    for key, val in integrity.items():
        if val != 0:
            integrity_ok = False
            print('   ' + key + ': ' + str(val) + ' (should be 0)')
    print('G. All §5.6 integrity fields are zero:', 'PASS' if integrity_ok else 'FAIL')
    if not integrity_ok:
        print('   Integrity:', json.dumps(integrity, indent=2))
    
    # H. All required §5.6 invariants pass
    print()
    print('H. §5.6 Invariants:')
    
    # Invariant 1: sum(action_breakdown.values()) == event_count
    action_breakdown = metrics.get('action_breakdown', {})
    action_sum = sum(action_breakdown.values())
    inv1 = action_sum == metrics['event_count']
    print('   Invariant 1 (sum action_breakdown == event_count):', 'PASS' if inv1 else 'FAIL', '(' + str(action_sum) + ' == ' + str(metrics['event_count']) + ')')
    
    # Invariant 2: sum(outcome_breakdown.values()) == event_count
    outcome_breakdown = metrics.get('outcome_breakdown', {})
    outcome_sum = sum(outcome_breakdown.values())
    inv2 = outcome_sum == metrics['event_count']
    print('   Invariant 2 (sum outcome_breakdown == event_count):', 'PASS' if inv2 else 'FAIL', '(' + str(outcome_sum) + ' == ' + str(metrics['event_count']) + ')')
    
    # Invariant 3: addressable + simulated_outreach + deferred + withheld + escalated == at_risk
    amounts = metrics.get('amounts_inr', {})
    partition_sum = (amounts.get('addressable', 0) + amounts.get('simulated_outreach', 0) + 
                     amounts.get('deferred', 0) + amounts.get('withheld', 0) + 
                     amounts.get('escalated', 0))
    at_risk = amounts.get('at_risk', 0)
    inv3 = abs(partition_sum - at_risk) <= 0.01  # within 1 paise
    print('   Invariant 3 (partition sum == at_risk):', 'PASS' if inv3 else 'FAIL', 
          '(' + str(round(partition_sum, 2)) + ' == ' + str(round(at_risk, 2)) + ')')
    
    # Invariant 4: recovered + failed + api_error == retry_now count
    retry_now = metrics.get('action_breakdown', {}).get('retry_now', 0)
    recovered = metrics.get('outcome_breakdown', {}).get('recovered', 0)
    failed = metrics.get('outcome_breakdown', {}).get('failed', 0)
    api_error = metrics.get('outcome_breakdown', {}).get('api_error', 0)
    outcome_sum_retry = recovered + failed + api_error
    inv4 = outcome_sum_retry == retry_now
    print('   Invariant 4 (recovered+failed+api_error == retry_now):', 'PASS' if inv4 else 'FAIL',
          '(' + str(outcome_sum_retry) + ' == ' + str(retry_now) + ')')
    
    # Invariant 5: simulated == nudge
    simulated = metrics.get('outcome_breakdown', {}).get('simulated', 0)
    nudge = metrics.get('action_breakdown', {}).get('nudge', 0)
    inv5 = simulated == nudge
    print('   Invariant 5 (simulated == nudge):', 'PASS' if inv5 else 'FAIL', 
          '(' + str(simulated) + ' == ' + str(nudge) + ')')
    
    # Invariant 6: pending + paused == retry_later
    retry_later = metrics.get('action_breakdown', {}).get('retry_later', 0)
    pending = metrics.get('outcome_breakdown', {}).get('pending', 0)
    paused = metrics.get('outcome_breakdown', {}).get('paused', 0)
    inv6 = (pending + paused) == retry_later
    print('   Invariant 6 (pending+paused == retry_later):', 'PASS' if inv6 else 'FAIL',
          '(' + str(pending+paused) + ' == ' + str(retry_later) + ')')
    
    # Invariant 7: escalated == escalate_to_human
    escalated = metrics.get('outcome_breakdown', {}).get('escalated', 0)
    escalate_human = metrics.get('action_breakdown', {}).get('escalate_to_human', 0)
    inv7 = escalated == escalate_human
    print('   Invariant 7 (escalated == escalate_to_human):', 'PASS' if inv7 else 'FAIL',
          '(' + str(escalated) + ' == ' + str(escalate_human) + ')')
    
    # Invariant 8: withheld == stop
    withheld = metrics.get('outcome_breakdown', {}).get('withheld', 0)
    stop = metrics.get('action_breakdown', {}).get('stop', 0)
    inv8 = withheld == stop
    print('   Invariant 8 (withheld == stop):', 'PASS' if inv8 else 'FAIL',
          '(' + str(withheld) + ' == ' + str(stop) + ')')
    
    # Invariant 9: integrity all zero
    integrity = metrics.get('integrity', {})
    inv9 = all(v == 0 for v in integrity.values())
    print('   Invariant 9 (all integrity == 0):', 'PASS' if inv9 else 'FAIL')
    
    # Invariant 10: out_of_bounds == 0 and missing_rationale == 0
    bounded = metrics.get('boundedness', {})
    inv10 = bounded.get('out_of_bounds_action_count', 1) == 0 and bounded.get('missing_rationale_count', 1) == 0
    print('   Invariant 10 (out_of_bounds=0, missing_rationale=0):', 'PASS' if inv10 else 'FAIL')
    
    print()
    all_invariants = all([inv1, inv2, inv3, inv4, inv5, inv6, inv7, inv8, inv9, inv10])
    print('All invariants PASS:', 'YES' if all_invariants else 'NO')