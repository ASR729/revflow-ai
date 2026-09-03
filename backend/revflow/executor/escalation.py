"""
RevFlow Executor — Escalation Queue Writer.

Per §3.5: Write-only from executor, read-only from UI.
flag_for_human is terminal with no state beyond it.
"""
from datetime import datetime, timezone

from revflow.contracts.enums import LadderStep
from revflow.ingestion.normaliser import Event
from revflow.db.connection import get_connection


def write_escalation(
    run_id: str,
    audit_log_id: int,
    event: Event,
    rule_fired: str,
    ladder_step: LadderStep,
    queue: str = "ops_review",
) -> int:
    """
    Write escalation row for events requiring human review.

    Args:
        run_id: Batch run ID
        audit_log_id: The audit_log row that triggered escalation
        event: The event being escalated
        rule_fired: The rule_fired that caused escalation
        ladder_step: Current ladder step (flag_for_human for B2B exhaustion)
        queue: "ops_review" or "finance_review"

    Returns:
        Escalation row ID
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO escalations (
                audit_log_id, reason, ladder_step, queue, created_at
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                audit_log_id,
                rule_fired,
                ladder_step.value,
                queue,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cursor.lastrowid