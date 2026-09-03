"""
RevFlow Summary Metrics — compute summary_metrics.json per §5.6.

All formulas from §5.2, §5.3, §5.4, §5.5.
All ten invariants from §5.6 asserted.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from revflow.db.connection import get_connection
from revflow.contracts.enums import Action, Outcome

SUMMARY_METRICS_PATH = Path("backend/data/summary_metrics.json")


def compute_summary_metrics(run_id: str, llm_mode: str = "live") -> Dict[str, Any]:
    """
    Compute all summary metrics for a run and write to JSON.

    Returns the metrics dict.
    """
    with get_connection() as conn:
        # Get run info
        run = conn.execute(
            "SELECT * FROM batch_runs WHERE run_id = ?", (run_id,)
        ).fetchone()

        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Get all audit_log rows for this run
        audit_rows = conn.execute(
            "SELECT * FROM audit_log WHERE run_id = ?", (run_id,)
        ).fetchall()

        # Get all events for this run
        event_rows = conn.execute(
            "SELECT * FROM events WHERE run_id = ?", (run_id,)
        ).fetchall()

        # Get contact_log for harassment incidents
        contact_rows = conn.execute(
            "SELECT customer_id, contact_date, COUNT(*) as cnt "
            "FROM contact_log WHERE run_id = ? "
            "GROUP BY customer_id, contact_date",
            (run_id,)
        ).fetchall()

    # ─── Amount calculations (§5.2) ────────────────────────────────────────
    at_risk_inr = sum(e["amount_inr"] for e in event_rows)

    # Partition by action
    action_amounts = {a.value: 0 for a in Action}
    action_counts = {a.value: 0 for a in Action}
    outcome_counts = {o.value: 0 for o in Outcome}

    for row in audit_rows:
        action = row["action"]
        outcome = row["outcome"]
        amount = row["amount_inr"]

        action_amounts[action] += amount
        action_counts[action] += 1
        outcome_counts[outcome] += 1

    addressable_inr = action_amounts.get(Action.RETRY_NOW.value, 0)
    simulated_outreach_inr = action_amounts.get(Action.NUDGE.value, 0)
    deferred_inr = action_amounts.get(Action.RETRY_LATER.value, 0)
    withheld_inr = action_amounts.get(Action.STOP.value, 0)
    escalated_inr = action_amounts.get(Action.ESCALATE_TO_HUMAN.value, 0)

    # Realised recovery (only from recovered outcomes)
    realised_recovered_inr = sum(
        row["attributed_recovery_inr"]
        for row in audit_rows
        if row["outcome"] == Outcome.RECOVERED.value
    )

    # ─── Rate calculations (§5.3) ──────────────────────────────────────────
    def safe_div(num: float, den: float) -> float | None:
        return num / den if den != 0 else None

    recovery_rate_realised = safe_div(realised_recovered_inr, addressable_inr)
    addressable_coverage = safe_div(addressable_inr, at_risk_inr)
    retry_success_rate = safe_div(
        outcome_counts.get(Outcome.RECOVERED.value, 0),
        action_counts.get(Action.RETRY_NOW.value, 0)
    )

    # ─── Per-pipeline metrics ──────────────────────────────────────────────
    by_pipeline = {}
    for event_type in EventType:
        et_rows = [r for r in audit_rows if r["event_type"] == event_type.value]
        et_events = [e for e in event_rows if e["event_type"] == event_type.value]

        et_at_risk = sum(e["amount_inr"] for e in et_events)
        et_addressable = sum(r["amount_inr"] for r in et_rows if r["action"] == Action.RETRY_NOW.value)
        et_recovered = sum(
            r["attributed_recovery_inr"]
            for r in et_rows
            if r["outcome"] == Outcome.RECOVERED.value
        )
        et_rate = safe_div(et_recovered, et_addressable)

        # b2b_receivable has no retry_now path → rate is null by design
        if event_type == EventType.B2B_RECEIVABLE:
            et_rate = None

        by_pipeline[event_type.value] = {
            "event_count": len(et_events),
            "at_risk_inr": round(et_at_risk / 100, 2),
            "addressable_inr": round(et_addressable / 100, 2),
            "realised_recovered_inr": round(et_recovered / 100, 2),
            "recovery_rate_realised": et_rate,
        }

    # ─── Boundedness metrics (§5.4) ────────────────────────────────────────
    total_events = len(event_rows)
    deterministic_count = sum(
        1 for r in audit_rows if r["llm_calls_used"] == 0
    )
    deterministic_share = deterministic_count / total_events if total_events > 0 else 0.0

    llm_call_count = sum(r["llm_calls_used"] for r in audit_rows)

    # Out-of-bounds actions
    allowed_actions = {a.value for a in Action}
    out_of_bounds = sum(
        1 for r in audit_rows if r["action"] not in allowed_actions
    )

    # Missing rationale
    missing_rationale = sum(
        1 for r in audit_rows if not r["rationale"] or len(r["rationale"]) < 10
    )

    # P95 decision latency
    latencies = sorted(r["latency_ms"] for r in audit_rows)
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0

    boundedness = {
        "withheld_count": action_counts.get(Action.STOP.value, 0),
        "escalated_count": action_counts.get(Action.ESCALATE_TO_HUMAN.value, 0),
        "deterministic_share": round(deterministic_share, 4),
        "llm_call_count": llm_call_count,
        "llm_call_budget": LLM_CALL_BUDGET_PER_RUN,
        "out_of_bounds_action_count": out_of_bounds,
        "missing_rationale_count": missing_rationale,
        "p95_decision_latency_ms": p95_latency,
    }

    # ─── Integrity metrics (§5.5) ──────────────────────────────────────────
    # False positives: action in (retry_now, nudge) AND true_cause in STOP_IF_CAUSE_IN
    from revflow.contracts.config import STOP_IF_CAUSE_IN

    stop_causes = set(STOP_IF_CAUSE_IN)

    # Build event_id -> true_cause map
    true_cause_map = {e["event_id"]: e["true_cause"] for e in event_rows if e["true_cause"]}

    false_positive_count = 0
    false_positive_cost = 0
    for row in audit_rows:
        if row["action"] in (Action.RETRY_NOW.value, Action.NUDGE.value):
            true_cause = true_cause_map.get(row["event_id"])
            if true_cause in stop_causes:
                false_positive_count += 1
                false_positive_cost += row["amount_inr"]

    # Harassment incidents: contact_log entries exceeding daily cap
    from revflow.contracts.config import MAX_CONTACTS_PER_CUSTOMER_PER_DAY
    harassment_incidents = sum(
        1 for r in contact_rows if r["cnt"] > MAX_CONTACTS_PER_CUSTOMER_PER_DAY
    )

    # Over-retry: retry_now where retry_count >= MAX_RETRIES
    from revflow.contracts.config import MAX_RETRIES
    over_retry_count = 0
    for row in audit_rows:
        if row["action"] == Action.RETRY_NOW.value:
            event = next((e for e in event_rows if e["event_id"] == row["event_id"]), None)
            if event and event["retry_count"] >= MAX_RETRIES:
                over_retry_count += 1

    integrity = {
        "false_positive_count": false_positive_count,
        "false_positive_cost_inr": round(false_positive_cost / 100, 2),
        "harassment_incident_count": harassment_incidents,
        "over_retry_count": over_retry_count,
    }

    # ─── Action/Outcome breakdowns ────────────────────────────────────────
    action_breakdown = {a.value: action_counts.get(a.value, 0) for a in Action}
    outcome_breakdown = {o.value: outcome_counts.get(o.value, 0) for o in Outcome}

    # ─── Assemble final metrics ───────────────────────────────────────────
    metrics = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": run["random_seed"],
        "llm_mode": llm_mode,
        "event_count": total_events,
        "amounts_inr": {
            "at_risk": round(at_risk_inr / 100, 2),
            "addressable": round(addressable_inr / 100, 2),
            "realised_recovered": round(realised_recovered_inr / 100, 2),
            "simulated_outreach": round(simulated_outreach_inr / 100, 2),
            "deferred": round(deferred_inr / 100, 2),
            "withheld": round(withheld_inr / 100, 2),
            "escalated": round(escalated_inr / 100, 2),
        },
        "rates": {
            "recovery_rate_realised": recovery_rate_realised,
            "addressable_coverage": addressable_coverage,
            "retry_success_rate": retry_success_rate,
        },
        "by_pipeline": by_pipeline,
        "boundedness": boundedness,
        "integrity": integrity,
        "action_breakdown": action_breakdown,
        "outcome_breakdown": outcome_breakdown,
    }

    # ─── Assert invariants (§5.6) ─────────────────────────────────────────
    _assert_invariants(metrics, action_amounts, outcome_counts, action_counts, at_risk_inr)

    # Write to file
    with open(SUMMARY_METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def _assert_invariants(
    metrics: dict,
    action_amounts: dict,
    outcome_counts: dict,
    action_counts: dict,
    at_risk_inr: int
) -> None:
    """Assert all ten invariants from §5.6."""

    # 1. sum(action_breakdown.values()) == event_count
    assert sum(metrics["action_breakdown"].values()) == metrics["event_count"], "Invariant 1 failed"

    # 2. sum(outcome_breakdown.values()) == event_count
    assert sum(metrics["outcome_breakdown"].values()) == metrics["event_count"], "Invariant 2 failed"

    # 3. addressable + simulated_outreach + deferred + withheld + escalated == at_risk (within 1 paise)
    amounts = metrics["amounts_inr"]
    partition_sum = (
        amounts["addressable"] * 100 +  # back to paise
        amounts["simulated_outreach"] * 100 +
        amounts["deferred"] * 100 +
        amounts["withheld"] * 100 +
        amounts["escalated"] * 100
    )
    assert abs(partition_sum - at_risk_inr) <= 1, f"Invariant 3 failed: {partition_sum} != {at_risk_inr}"

    # 4. recovered + failed + api_error == action_breakdown.retry_now
    retry_now_count = metrics["action_breakdown"]["retry_now"]
    outcome_sum = (
        metrics["outcome_breakdown"]["recovered"] +
        metrics["outcome_breakdown"]["failed"] +
        metrics["outcome_breakdown"]["api_error"]
    )
    assert outcome_sum == retry_now_count, "Invariant 4 failed"

    # 5. simulated == action_breakdown.nudge
    assert metrics["outcome_breakdown"]["simulated"] == metrics["action_breakdown"]["nudge"], "Invariant 5 failed"

    # 6. pending + paused == action_breakdown.retry_later
    retry_later_count = metrics["action_breakdown"]["retry_later"]
    pending_paused = (
        metrics["outcome_breakdown"]["pending"] +
        metrics["outcome_breakdown"]["paused"]
    )
    assert pending_paused == retry_later_count, "Invariant 6 failed"

    # 7. escalated == action_breakdown.escalate_to_human
    assert metrics["outcome_breakdown"]["escalated"] == metrics["action_breakdown"]["escalate_to_human"], "Invariant 7 failed"

    # 8. withheld == action_breakdown.stop
    assert metrics["outcome_breakdown"]["withheld"] == metrics["action_breakdown"]["stop"], "Invariant 8 failed"

    # 9. every value under integrity is 0
    for key, val in metrics["integrity"].items():
        assert val == 0, f"Invariant 9 failed: integrity.{key} = {val}"

    # 10. out_of_bounds_action_count == 0 and missing_rationale_count == 0
    assert metrics["boundedness"]["out_of_bounds_action_count"] == 0, "Invariant 10a failed"
    assert metrics["boundedness"]["missing_rationale_count"] == 0, "Invariant 10b failed"


from datetime import datetime, timezone
from revflow.contracts.enums import EventType
from revflow.contracts.config import LLM_CALL_BUDGET_PER_RUN
import json