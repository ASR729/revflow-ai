"""
RevFlow Policy Engine — Stage 3: Deterministic Action Table.

Per §4.3: 21 rows evaluated top to bottom, first match wins.
Returns (action, ladder_step, rule_fired) or None if no match (→ Stage 4).

All values from enums — no hardcoded strings.
"""
from datetime import datetime
from typing import Optional, Tuple

from revflow.contracts.config import (
    MAX_RETRIES,
    LADDER_GENTLE_AFTER_DAYS,
    LADDER_FIRM_AFTER_DAYS,
    LADDER_FLAG_AFTER_DAYS,
)
from revflow.contracts.enums import (
    EventType, Cause, Action, LadderStep, RuleFired,
    validate_ladder_action
)
from revflow.ingestion.normaliser import Event
from revflow.ladder.b2b import assign_ladder_step, advance_ladder_step


def invoice_age_days(event: Event, as_of: datetime) -> int:
    """
    Compute invoice age in days past due.
    Per §3.2: derived, never stored. (run_date - invoice_due_date) in whole days.
    """
    if not event.invoice_due_date:
        return 0
    due_date = datetime.fromisoformat(event.invoice_due_date.replace('Z', '+00:00')).date()
    run_date = as_of.date()
    return (run_date - due_date).days


def resolve_action_table(event: Event, cause: Cause, as_of: datetime) -> Optional[Tuple[Action, LadderStep, RuleFired]]:
    """
    Stage 3: Deterministic action table lookup (§4.3).

    Evaluates rows 1-21 in order. First match wins.
    Returns (action, ladder_step, rule_fired) or None if no match (→ Stage 4).

    Note: Rows 1-2 (hard stops) are handled in Stage 1.
    Row 3 (retry ceiling) is handled in Stage 2a.
    """
    et = event.event_type
    c = cause
    rc = event.retry_count
    age = invoice_age_days(event, as_of)
    current_ladder = LadderStep(event.ladder_step)

    # Row 4: checkout_dropoff + technical_decline → retry_now
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.TECHNICAL_DECLINE:
        return (Action.RETRY_NOW, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 5: checkout_dropoff + bank_timeout → retry_now
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.BANK_TIMEOUT:
        return (Action.RETRY_NOW, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 6: checkout_dropoff + insufficient_funds + retry_count == 0 → retry_later
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.INSUFFICIENT_FUNDS and rc == 0:
        return (Action.RETRY_LATER, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 7: checkout_dropoff + insufficient_funds + retry_count >= 1 → nudge
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.INSUFFICIENT_FUNDS and rc >= 1:
        return (Action.NUDGE, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 8: checkout_dropoff + business_decline → nudge
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.BUSINESS_DECLINE:
        return (Action.NUDGE, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 9: checkout_dropoff + authentication_failed → nudge
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.AUTHENTICATION_FAILED:
        return (Action.NUDGE, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 10: checkout_dropoff + session_timeout → nudge
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.SESSION_TIMEOUT:
        return (Action.NUDGE, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 11: checkout_dropoff + user_abandoned → nudge
    if et == EventType.CHECKOUT_DROPOFF and c == Cause.USER_ABANDONED:
        return (Action.NUDGE, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 12: subscription_failure + bank_timeout → retry_now
    if et == EventType.SUBSCRIPTION_FAILURE and c == Cause.BANK_TIMEOUT:
        return (Action.RETRY_NOW, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 13: subscription_failure + technical_decline → retry_now
    if et == EventType.SUBSCRIPTION_FAILURE and c == Cause.TECHNICAL_DECLINE:
        return (Action.RETRY_NOW, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 14: subscription_failure + insufficient_funds → retry_later
    if et == EventType.SUBSCRIPTION_FAILURE and c == Cause.INSUFFICIENT_FUNDS:
        return (Action.RETRY_LATER, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 15: subscription_failure + mandate_expired → nudge
    if et == EventType.SUBSCRIPTION_FAILURE and c == Cause.MANDATE_EXPIRED:
        return (Action.NUDGE, LadderStep.NONE, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 16: b2b_receivable + awaiting_po → escalate_to_human + flag_for_human
    if et == EventType.B2B_RECEIVABLE and c == Cause.AWAITING_PO:
        return (Action.ESCALATE_TO_HUMAN, LadderStep.FLAG_FOR_HUMAN, RuleFired.DETERMINISTIC_ACTION_TABLE)

    # Row 17-20: b2b_receivable + invoice_overdue + age bands (ladder monotonicity)
    if et == EventType.B2B_RECEIVABLE and c == Cause.INVOICE_OVERDUE:
        # Use ladder module for canonical ladder logic
        max_allowed = assign_ladder_step(event, c, as_of)
        next_ladder = advance_ladder_step(current_ladder, max_allowed)

        if age >= LADDER_FLAG_AFTER_DAYS:  # >= 45
            return (Action.ESCALATE_TO_HUMAN, next_ladder, RuleFired.LADDER_STEP_BY_AGE)
        elif age >= LADDER_FIRM_AFTER_DAYS:  # 21-44
            return (Action.NUDGE, next_ladder, RuleFired.LADDER_STEP_BY_AGE)
        elif age >= LADDER_GENTLE_AFTER_DAYS:  # 7-20
            return (Action.NUDGE, next_ladder, RuleFired.LADDER_STEP_BY_AGE)
        else:  # age < 7
            return (Action.RETRY_LATER, LadderStep.NONE, RuleFired.LADDER_NOT_YET_DUE)

    # Row 21: any + unclassified → Stage 4 (LLM)
    if c == Cause.UNCLASSIFIED:
        return None

    # No matching row → Stage 4
    return None


from datetime import datetime