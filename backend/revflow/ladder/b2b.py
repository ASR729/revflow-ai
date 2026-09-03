"""
RevFlow B2B Ladder — Step assignment and monotonic advancement.

Per §4.3 and §2.4:
- Ladder steps: none → gentle_reminder → firm_reminder → flag_for_human
- Advancement by exactly ONE step per decision (monotonicity)
- Age thresholds determine MAXIMUM step reachable, not the step assigned
- Hard stops can interrupt at any point
"""
from datetime import datetime

from revflow.contracts.config import (
    LADDER_GENTLE_AFTER_DAYS,
    LADDER_FIRM_AFTER_DAYS,
    LADDER_FLAG_AFTER_DAYS,
)
from revflow.contracts.enums import EventType, Cause, LadderStep, Action
from revflow.ingestion.normaliser import Event


def invoice_age_days(event: Event, as_of: datetime) -> int:
    """Compute invoice age in whole days past due."""
    if not event.invoice_due_date:
        return 0
    due_date = datetime.fromisoformat(event.invoice_due_date.replace('Z', '+00:00')).date()
    return (as_of.date() - due_date).days


def assign_ladder_step(event: Event, cause: Cause, as_of: datetime) -> LadderStep:
    """
    Assign ladder step based on invoice age (§4.3 rows 17-20).

    Returns the MAXIMUM step reachable by age, not the step to assign.
    The actual step assigned is min(current_step + 1, max_reachable).
    """
    if event.event_type != EventType.B2B_RECEIVABLE:
        return LadderStep.NONE

    if cause != Cause.INVOICE_OVERDUE:
        return LadderStep.NONE

    age = invoice_age_days(event, as_of)

    if age >= LADDER_FLAG_AFTER_DAYS:  # >= 45
        return LadderStep.FLAG_FOR_HUMAN
    elif age >= LADDER_FIRM_AFTER_DAYS:  # 21-44
        return LadderStep.FIRM_REMINDER
    elif age >= LADDER_GENTLE_AFTER_DAYS:  # 7-20
        return LadderStep.GENTLE_REMINDER
    else:  # age < 7
        return LadderStep.NONE


def advance_ladder_step(current: LadderStep, max_reachable: LadderStep) -> LadderStep:
    """
    Advance ladder step by exactly ONE per decision (monotonicity per §4.3).

    Args:
        current: Current ladder_step of the event.
        max_reachable: Maximum step reachable by age (from assign_ladder_step).

    Returns:
        Next ladder step, capped at max_reachable.
    """
    # If already at or above max, don't advance
    step_order = {
        LadderStep.NONE: 0,
        LadderStep.GENTLE_REMINDER: 1,
        LadderStep.FIRM_REMINDER: 2,
        LadderStep.FLAG_FOR_HUMAN: 3,
    }

    current_order = step_order[current]
    max_order = step_order[max_reachable]

    if current_order >= max_order:
        return current  # Already at or above max

    # Advance by exactly one
    next_order = current_order + 1
    if next_order > max_order:
        next_order = max_order

    for step, order in step_order.items():
        if order == next_order:
            return step

    return max_reachable


def get_action_for_ladder_step(ladder_step: LadderStep) -> tuple[Action, str]:
    """
    Get the paired action for a ladder step (per §2.4).

    Returns:
        (action, rule_fired)
    """
    if ladder_step == LadderStep.GENTLE_REMINDER:
        return Action.NUDGE, "ladder_step_by_age"
    elif ladder_step == LadderStep.FIRM_REMINDER:
        return Action.NUDGE, "ladder_step_by_age"
    elif ladder_step == LadderStep.FLAG_FOR_HUMAN:
        return Action.ESCALATE_TO_HUMAN, "ladder_step_by_age"
    else:
        return Action.RETRY_LATER, "ladder_not_yet_due"