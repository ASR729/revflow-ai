"""
RevFlow Ledger — Single write path to audit_log.

Per §3.3 and DB-5: insert_audit_row() is the ONLY function anywhere that writes to audit_log.
Verified by grep: no other INSERT into audit_log exists.
"""
import time
import sqlite3
from typing import Optional

from revflow.db.connection import get_connection
from revflow.contracts.enums import (
    Action,
    Outcome,
    LadderStep,
    CauseSource,
    RuleFired,
    validate_action_outcome,
)


def insert_audit_row(
    run_id: str,
    event_id: str,
    event_type: str,
    cause: str,
    cause_source: str,
    rule_fired: str,
    action: str,
    ladder_step: str,
    rationale: str,
    outcome: str,
    amount_inr: int,
    attributed_recovery_inr: int = 0,
    is_simulated: int = 0,
    llm_calls_used: int = 0,
) -> int:
    """
    Insert a single audit_log row. This is the ONLY write path to audit_log.

    Args:
        run_id: Batch run identifier
        event_id: Event identifier
        event_type: Event type (denormalized)
        cause: Root cause
        cause_source: 'rule' or 'llm'
        rule_fired: Rule that authorized the decision
        action: Action taken
        ladder_step: Current ladder step
        rationale: Human-readable reason (length >= 10)
        outcome: Outcome of the action
        amount_inr: Amount in paise at decision time
        attributed_recovery_inr: Recovery amount in paise (non-zero only for 'recovered')
        is_simulated: 1 if action='nudge', else 0
        llm_calls_used: 0, 1, or 2

    Returns:
        The autoincrement ID of the inserted row.

    Raises:
        ValueError: If action/outcome pairing is invalid per §2.5
        ValueError: If rationale is too short (< 10 chars) per FR-7
    """
    # Validate action/outcome pairing per §2.5
    # Note: For retry_now, initial outcome is 'pending' (pre-execution), which is updated by executor
    try:
        action_enum = Action(action)
        outcome_enum = Outcome(outcome)
    except ValueError:
        pass  # Let DB constraint catch invalid enum values
    else:
        # Allow 'pending' for retry_now as initial pre-execution state
        if not (action == Action.RETRY_NOW.value and outcome == Outcome.PENDING.value):
            if not validate_action_outcome(action_enum, outcome_enum):
                raise ValueError(f"Invalid action/outcome pairing: {action}/{outcome}")

    # Validate rationale length per FR-7
    if not rationale or len(rationale) < 10:
        raise ValueError("Rationale must be at least 10 characters (FR-7)")

    # Validate attributed_recovery_inr only for recovered outcome
    if outcome == Outcome.RECOVERED.value and attributed_recovery_inr <= 0:
        raise ValueError("attributed_recovery_inr must be > 0 when outcome='recovered'")
    if outcome != Outcome.RECOVERED.value and attributed_recovery_inr != 0:
        raise ValueError("attributed_recovery_inr must be 0 when outcome != 'recovered'")

    # Validate is_simulated matches action
    if action == Action.NUDGE.value and is_simulated != 1:
        raise ValueError("is_simulated must be 1 when action='nudge'")
    if action != Action.NUDGE.value and is_simulated != 0:
        raise ValueError("is_simulated must be 0 when action != 'nudge'")

    start = time.perf_counter()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO audit_log (
                run_id, event_id, event_type, cause, cause_source, rule_fired,
                action, ladder_step, rationale, outcome, amount_inr,
                attributed_recovery_inr, is_simulated, llm_calls_used, latency_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                run_id,
                event_id,
                event_type,
                cause,
                cause_source,
                rule_fired,
                action,
                ladder_step,
                rationale,
                outcome,
                amount_inr,
                attributed_recovery_inr,
                is_simulated,
                llm_calls_used,
                0,  # latency_ms will be updated below
            ),
        )
        audit_id = cursor.lastrowid

        # Update latency_ms with actual elapsed time
        latency_ms = int((time.perf_counter() - start) * 1000)
        conn.execute(
            "UPDATE audit_log SET latency_ms = ? WHERE id = ?",
            (latency_ms, audit_id),
        )

    return audit_id


# ─── Read helpers for API endpoints ───────────────────────────────────────────


def get_audit_log_rows(
    run_id: Optional[str] = None,
    event_type: Optional[str] = None,
    cause: Optional[str] = None,
    action: Optional[str] = None,
    sort: str = "timestamp",
    order: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[sqlite3.Row], int]:
    """Get paginated, filterable audit log rows with total count."""
    with get_connection() as conn:
        # Build WHERE clause
        where_clauses = []
        params = []

        if run_id:
            where_clauses.append("al.run_id = ?")
            params.append(run_id)
        if event_type:
            where_clauses.append("al.event_type = ?")
            params.append(event_type)
        if cause:
            where_clauses.append("al.cause = ?")
            params.append(cause)
        if action:
            where_clauses.append("al.action = ?")
            params.append(action)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Validate sort column
        sort_map = {
            "amount": "amount_inr",
            "cause": "cause",
            "timestamp": "created_at",
        }
        sort_col = sort_map.get(sort, "created_at")
        order_sql = "DESC" if order.lower() == "desc" else "ASC"

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM audit_log al {where_sql}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # Get rows with joins for customer_id, decline_code, simulated_channel
        query = f"""
            SELECT
                al.*,
                e.customer_id,
                e.decline_code,
                sa.channel as simulated_channel
            FROM audit_log al
            JOIN events e ON al.event_id = e.event_id
            LEFT JOIN simulated_actions sa ON sa.audit_log_id = al.id
            {where_sql}
            ORDER BY al.{sort_col} {order_sql}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()

    return rows, total


def get_exceptions(run_id: Optional[str] = None) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    """Get pre-grouped exceptions: withheld_by_policy (action=stop) and needs_a_human (action=escalate_to_human)."""
    with get_connection() as conn:
        where = "WHERE 1=1"
        params = []
        if run_id:
            where += " AND al.run_id = ?"
            params.append(run_id)

        withheld = conn.execute(
            f"""
            SELECT al.*, e.customer_id, e.decline_code, sa.channel as simulated_channel
            FROM audit_log al
            JOIN events e ON al.event_id = e.event_id
            LEFT JOIN simulated_actions sa ON sa.audit_log_id = al.id
            {where} AND al.action = 'stop'
            ORDER BY al.created_at DESC
            """,
            params,
        ).fetchall()

        needs_human = conn.execute(
            f"""
            SELECT al.*, e.customer_id, e.decline_code, sa.channel as simulated_channel
            FROM audit_log al
            JOIN events e ON al.event_id = e.event_id
            LEFT JOIN simulated_actions sa ON sa.audit_log_id = al.id
            {where} AND al.action = 'escalate_to_human'
            ORDER BY al.created_at DESC
            """,
            params,
        ).fetchall()

    return withheld, needs_human


def get_event_detail(event_id: str) -> Optional[sqlite3.Row]:
    """Get full event detail for Event Detail Drawer."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()


def get_audit_timeline(event_id: str) -> list[sqlite3.Row]:
    """Get all audit_log rows for an event, chronological."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT al.*, e.customer_id, e.decline_code, sa.channel as simulated_channel
            FROM audit_log al
            JOIN events e ON al.event_id = e.event_id
            LEFT JOIN simulated_actions sa ON sa.audit_log_id = al.id
            WHERE al.event_id = ?
            ORDER BY al.created_at ASC""",
            (event_id,),
        ).fetchall()


def get_simulated_actions(audit_log_id: int) -> list[sqlite3.Row]:
    """Get simulated_actions for an audit_log row."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM simulated_actions WHERE audit_log_id = ?",
            (audit_log_id,),
        ).fetchall()


def get_escalations(audit_log_id: int) -> list[sqlite3.Row]:
    """Get escalations for an audit_log row."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM escalations WHERE audit_log_id = ?",
            (audit_log_id,),
        ).fetchall()


def get_ptp_commitments(event_id: str) -> list[sqlite3.Row]:
    """Get PTP commitments for an event."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM ptp_commitments WHERE event_id = ? ORDER BY created_at ASC",
            (event_id,),
        ).fetchall()