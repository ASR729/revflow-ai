"""
RevFlow Policy Engine — Stage 2: Guard Checks.

Per §4.2: Stage 2 executes after Stage 1, before Stage 3. Deterministic, DB reads only, short-circuits.

Four guards in order:
2a. Retry ceiling: retry_count >= MAX_RETRIES → escalate_to_human
2b. PTP pause / broken promise: check paused_until and ptp_commitments
2c. Cooldown: last_attempt_at within COOLDOWN_HOURS → retry_later
2d. Contact-frequency cap: contacts today >= MAX_CONTACTS_PER_CUSTOMER_PER_DAY → retry_later
"""
from datetime import datetime, timezone
from typing import Optional

from revflow.contracts.config import (
    MAX_RETRIES,
    COOLDOWN_HOURS,
    MAX_CONTACTS_PER_CUSTOMER_PER_DAY,
    PTP_GRACE_DAYS,
)
from revflow.contracts.enums import (
    Action, Outcome, RuleFired, LadderStep, Cause, PTPStatus
)
from revflow.ingestion.normaliser import Event
from revflow.db.connection import get_connection


def check_retry_ceiling(event: Event) -> Optional[dict]:
    """2a: Retry ceiling check."""
    if event.retry_count >= MAX_RETRIES:
        return {
            "action": Action.ESCALATE_TO_HUMAN,
            "outcome": Outcome.ESCALATED,
            "ladder_step": LadderStep(event.ladder_step),  # unchanged
            "rule_fired": RuleFired.RETRY_CEILING_REACHED,
            "rationale": f"Retry count {event.retry_count} >= MAX_RETRIES ({MAX_RETRIES}). Escalating to human.",
            "llm_calls_used": 0,
        }
    return None


def check_ptp_pause(event: Event, run_date: datetime) -> Optional[dict]:
    """2b: PTP pause / broken promise check."""
    # Check if event has a paused_until date
    if event.paused_until:
        paused_until = datetime.fromisoformat(event.paused_until.replace('Z', '+00:00'))
        if run_date <= paused_until:
            # Still within pause period
            return {
                "action": Action.RETRY_LATER,
                "outcome": Outcome.PAUSED,
                "ladder_step": LadderStep(event.ladder_step),
                "rule_fired": RuleFired.PTP_PAUSE_ACTIVE,
                "rationale": f"Active PTP pause until {event.paused_until}. Holding.",
                "llm_calls_used": 0,
            }
        else:
            # Past paused_until - check if promise was broken
            # This requires checking ptp_commitments table
            with get_connection() as conn:
                ptp = conn.execute(
                    "SELECT status, ladder_step_at_pause FROM ptp_commitments "
                    "WHERE event_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
                    (event.event_id,)
                ).fetchone()

                if ptp and ptp["status"] == PTPStatus.ACTIVE.value:
                    # Promise broken - escalate one step above ladder_step_at_pause
                    ladder_at_pause = LadderStep(ptp["ladder_step_at_pause"])

                    # Determine next step (advance by exactly one)
                    next_step = _advance_ladder_step(ladder_at_pause)

                    # Update ptp_commitments status to broken
                    conn.execute(
                        "UPDATE ptp_commitments SET status = ? WHERE event_id = ? AND status = ?",
                        (PTPStatus.BROKEN.value, event.event_id, PTPStatus.ACTIVE.value)
                    )

                    return {
                        "action": Action.ESCALATE_TO_HUMAN,
                        "outcome": Outcome.ESCALATED,
                        "ladder_step": next_step,
                        "rule_fired": RuleFired.PTP_PROMISE_BROKEN_ESCALATED,
                        "rationale": f"PTP promise broken (past {event.paused_until} + {PTP_GRACE_DAYS} days grace). Escalated one step above {ladder_at_pause.value}.",
                        "llm_calls_used": 0,
                    }

    # Check for new PTP from customer_reply_text
    if event.customer_reply_text:
        # PTP detection is handled separately (in ptp/tracker.py)
        # Here we just check if there's an active PTP commitment
        with get_connection() as conn:
            ptp = conn.execute(
                "SELECT promised_date, ladder_step_at_pause FROM ptp_commitments "
                "WHERE event_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
                (event.event_id,)
            ).fetchone()

            if ptp:
                promised_date = datetime.fromisoformat(ptp["promised_date"]).replace(tzinfo=timezone.utc)
                grace_end = promised_date + timedelta(days=PTP_GRACE_DAYS)

                if run_date <= grace_end:
                    # Pause active
                    return {
                        "action": Action.RETRY_LATER,
                        "outcome": Outcome.PAUSED,
                        "ladder_step": LadderStep(event.ladder_step),
                        "rule_fired": RuleFired.PTP_PAUSE_ACTIVE,
                        "rationale": f"Active PTP promise until {ptp['promised_date']}. Holding.",
                        "llm_calls_used": 0,
                    }
                else:
                    # Promise broken
                    ladder_at_pause = LadderStep(ptp["ladder_step_at_pause"])
                    next_step = _advance_ladder_step(ladder_at_pause)

                    conn.execute(
                        "UPDATE ptp_commitments SET status = ? WHERE event_id = ? AND status = ?",
                        (PTPStatus.BROKEN.value, event.event_id, PTPStatus.ACTIVE.value)
                    )

                    return {
                        "action": Action.ESCALATE_TO_HUMAN,
                        "outcome": Outcome.ESCALATED,
                        "ladder_step": next_step,
                        "rule_fired": RuleFired.PTP_PROMISE_BROKEN_ESCALATED,
                        "rationale": f"PTP promise broken. Escalated one step above {ladder_at_pause.value}.",
                        "llm_calls_used": 0,
                    }

    return None


def check_cooldown(event: Event, run_date: datetime) -> Optional[dict]:
    """2c: Cooldown check."""
    if event.last_attempt_at:
        last_attempt = datetime.fromisoformat(event.last_attempt_at.replace('Z', '+00:00'))
        hours_since = (run_date - last_attempt).total_seconds() / 3600
        if hours_since < COOLDOWN_HOURS:
            return {
                "action": Action.RETRY_LATER,
                "outcome": Outcome.PENDING,
                "ladder_step": LadderStep(event.ladder_step),
                "rule_fired": RuleFired.COOLDOWN_ACTIVE,
                "rationale": f"Last attempt {hours_since:.1f}h ago < COOLDOWN_HOURS ({COOLDOWN_HOURS}h). Cooling down.",
                "llm_calls_used": 0,
            }
    return None


def check_contact_cap(event: Event, run_date: datetime) -> Optional[dict]:
    """2d: Contact frequency cap check."""
    # Only applies if action would be 'nudge' (outbound contact)
    # The cap is checked at decision time based on contact_log
    run_date_str = run_date.date().isoformat()

    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM contact_log WHERE customer_id = ? AND contact_date = ?",
            (event.customer_id, run_date_str)
        ).fetchone()[0]

        if count >= MAX_CONTACTS_PER_CUSTOMER_PER_DAY:
            return {
                "action": Action.RETRY_LATER,
                "outcome": Outcome.PENDING,
                "ladder_step": LadderStep(event.ladder_step),
                "rule_fired": RuleFired.CONTACT_CAP_REACHED,
                "rationale": f"Customer {event.customer_id} already contacted {count} times today (cap: {MAX_CONTACTS_PER_CUSTOMER_PER_DAY}).",
                "llm_calls_used": 0,
            }
    return None


def _advance_ladder_step(current: LadderStep) -> LadderStep:
    """Advance ladder step by exactly one (monotonicity per §4.3)."""
    if current == LadderStep.NONE:
        return LadderStep.GENTLE_REMINDER
    elif current == LadderStep.GENTLE_REMINDER:
        return LadderStep.FIRM_REMINDER
    elif current == LadderStep.FIRM_REMINDER:
        return LadderStep.FLAG_FOR_HUMAN
    else:  # FLAG_FOR_HUMAN
        return LadderStep.FLAG_FOR_HUMAN


def check_guards(event: Event, run_date: datetime) -> Optional[dict]:
    """
    Stage 2: All guard checks in order.
    Returns first matching guard decision, or None if all pass.
    """
    # 2a: Retry ceiling
    result = check_retry_ceiling(event)
    if result:
        return result

    # 2b: PTP pause / broken promise
    result = check_ptp_pause(event, run_date)
    if result:
        return result

    # 2c: Cooldown
    result = check_cooldown(event, run_date)
    if result:
        return result

    # 2d: Contact frequency cap
    result = check_contact_cap(event, run_date)
    if result:
        return result

    return None


from datetime import timedelta