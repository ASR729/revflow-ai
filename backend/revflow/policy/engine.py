"""
RevFlow Policy Engine — Stage 4: Bounded LLM Action Selection.

Per §4.2, §4.3 Row 21: Only reached when Stage 3 returns no match
(cause = unclassified, or no matching (event_type, cause) row).

LLM receives allowed actions as closed list. Response validated in code.
Invalid/unparseable/timed-out/budget-exceeded → escalate_to_human.
"""
from datetime import datetime
from typing import Optional, List, Tuple

from revflow.contracts.enums import (
    EventType, Cause, Action, LadderStep, Outcome, RuleFired, CauseSource
)
from revflow.contracts.config import LLM_CALL_BUDGET_PER_RUN
from revflow.adapters.llm import get_llm_adapter
from revflow.ingestion.normaliser import Event
from revflow.db.connection import get_connection


# Allowed actions for LLM selection (closed list per §2.3)
ALL_ACTIONS = [a.value for a in Action]


def get_allowed_actions_for_stage4(event: Event, cause: Cause) -> List[str]:
    """
    Get allowed actions for LLM Stage 4.
    Excludes actions that would be invalid for this event/cause combo.
    """
    allowed = ALL_ACTIONS.copy()

    # Remove retry_now for b2b_receivable (no retry path per §4.3)
    if event.event_type == EventType.B2B_RECEIVABLE:
        allowed = [a for a in allowed if a != Action.RETRY_NOW.value]

    # Remove stop (hard stops already handled in Stage 1)
    allowed = [a for a in allowed if a != Action.STOP.value]

    return allowed


async def select_action_llm(
    event: Event,
    cause: Cause,
    run_id: str,
    as_of: datetime,
    llm_calls_used: int,
    use_llm: bool = True
) -> Tuple[Action, LadderStep, RuleFired, str, int]:
    """
    Stage 4: Bounded LLM action selection.

    Returns:
        (action, ladder_step, rule_fired, rationale, llm_calls_used)

    On failure/invalid/budget: returns escalate_to_human with rule_fired=llm_output_rejected_defaulted
    """
    # If LLM is disabled, immediately escalate to human
    if not use_llm:
        return (
            Action.ESCALATE_TO_HUMAN,
            LadderStep(event.ladder_step),
            RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
            "LLM disabled (offline mode); defaulted to escalate_to_human",
            llm_calls_used,
        )

    # Check budget
    with get_connection() as conn:
        run = conn.execute(
            "SELECT llm_call_count FROM batch_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if run and run["llm_call_count"] >= LLM_CALL_BUDGET_PER_RUN:
            return (
                Action.ESCALATE_TO_HUMAN,
                LadderStep(event.ladder_step),
                RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
                "LLM call budget exhausted for this run",
                llm_calls_used,
            )

    # Get allowed actions
    allowed_actions = get_allowed_actions_for_stage4(event, cause)

    # Get LLM adapter
    adapter = get_llm_adapter()

    # Call LLM
    result = await adapter.select_action(event, cause.value, allowed_actions)

    if result is None:
        # LLM unavailable, timeout, or failed
        return (
            Action.ESCALATE_TO_HUMAN,
            LadderStep(event.ladder_step),
            RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
            "LLM selection unavailable or timed out",
            llm_calls_used,
        )

    action_str, rationale = result
    llm_calls_used += 1

    # Validate action is in allowed list
    try:
        action = Action(action_str)
    except ValueError:
        return (
            Action.ESCALATE_TO_HUMAN,
            LadderStep(event.ladder_step),
            RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
            f"LLM returned invalid action: {action_str}",
            llm_calls_used,
        )

    if action.value not in allowed_actions:
        return (
            Action.ESCALATE_TO_HUMAN,
            LadderStep(event.ladder_step),
            RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
            f"LLM returned disallowed action: {action_str}",
            llm_calls_used,
        )

    # Validate rationale exists (FR-7)
    if not rationale or len(rationale) < 10:
        return (
            Action.ESCALATE_TO_HUMAN,
            LadderStep(event.ladder_step),
            RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
            "LLM returned empty or too short rationale",
            llm_calls_used,
        )

    # Determine ladder_step (unchanged unless action=nudge for B2B)
    ladder_step = LadderStep(event.ladder_step)
    if event.event_type == EventType.B2B_RECEIVABLE and action == Action.NUDGE:
        # Advance ladder step by one (monotonicity)
        current = LadderStep(event.ladder_step)
        if current == LadderStep.NONE:
            ladder_step = LadderStep.GENTLE_REMINDER
        elif current == LadderStep.GENTLE_REMINDER:
            ladder_step = LadderStep.FIRM_REMINDER
        elif current == LadderStep.FIRM_REMINDER:
            ladder_step = LadderStep.FLAG_FOR_HUMAN

    # Validate ladder_step/action pairing
    from revflow.contracts.enums import validate_ladder_action
    if not validate_ladder_action(ladder_step, action):
        return (
            Action.ESCALATE_TO_HUMAN,
            LadderStep(event.ladder_step),
            RuleFired.LLM_OUTPUT_REJECTED_DEFAULTED,
            f"Invalid ladder_step/action pairing: {ladder_step.value}/{action.value}",
            llm_calls_used,
        )

    # Update llm_call_count in batch_runs
    with get_connection() as conn:
        conn.execute(
            "UPDATE batch_runs SET llm_call_count = llm_call_count + 1 WHERE run_id = ?",
            (run_id,)
        )

    return (
        action,
        ladder_step,
        RuleFired.LLM_REASONED_WITHIN_CEILING,
        rationale,
        llm_calls_used,
    )


def decide_action(
    event: Event,
    cause: Cause,
    cause_source: CauseSource,
    run_id: str,
    as_of: datetime,
    llm_calls_used: int
) -> dict:
    """
    Main policy decision function — runs all four stages in order.

    Per §4.2: Stage 1 → Stage 2 → Stage 3 → Stage 4 (only if needed).
    Each stage short-circuits on match.

    Returns decision dict with:
        action, outcome, ladder_step, rule_fired, rationale, llm_calls_used
    """
    # Stage 1: Hard stops
    from .hard_stops import check_hard_stops
    result = check_hard_stops(event, cause)
    if result:
        result["cause_source"] = cause_source.value
        return result

    # Stage 2: Guards
    from .guards import check_guards
    result = check_guards(event, as_of)
    if result:
        result["cause_source"] = cause_source.value
        return result

    # Stage 3: Deterministic action table
    from .action_table import resolve_action_table
    table_result = resolve_action_table(event, cause, as_of)
    if table_result:
        action, ladder_step, rule_fired = table_result

        # Determine outcome based on action
        if action == Action.RETRY_NOW:
            outcome = Outcome.PENDING  # Will be updated by executor
        elif action == Action.RETRY_LATER:
            outcome = Outcome.PENDING
        elif action == Action.NUDGE:
            outcome = Outcome.SIMULATED
        elif action == Action.ESCALATE_TO_HUMAN:
            outcome = Outcome.ESCALATED
        elif action == Action.STOP:
            outcome = Outcome.WITHHELD
        else:
            outcome = Outcome.PENDING

        return {
            "action": action,
            "outcome": outcome,
            "ladder_step": ladder_step,
            "rule_fired": rule_fired,
            "rationale": f"Deterministic action table: {rule_fired.value}",
            "cause_source": cause_source.value,
            "llm_calls_used": llm_calls_used,
        }

    # Stage 4: Bounded LLM
    # This is async, but we need to run it synchronously here
    # The caller should handle the async call
    return {
        "stage": 4,
        "needs_llm": True,
        "cause_source": cause_source.value,
        "llm_calls_used": llm_calls_used,
    }


async def decide_action_async(
    event: Event,
    cause: Cause,
    cause_source: CauseSource,
    run_id: str,
    as_of: datetime,
    llm_calls_used: int,
    use_llm: bool = True
) -> dict:
    """
    Async version of decide_action that can call Stage 4 LLM.
    """
    # Stage 1
    from .hard_stops import check_hard_stops
    result = check_hard_stops(event, cause)
    if result:
        result["cause_source"] = cause_source.value
        return result

    # Stage 2
    from .guards import check_guards
    result = check_guards(event, as_of)
    if result:
        result["cause_source"] = cause_source.value
        return result

    # Stage 3
    from .action_table import resolve_action_table
    table_result = resolve_action_table(event, cause, as_of)
    if table_result:
        action, ladder_step, rule_fired = table_result

        if action == Action.RETRY_NOW:
            outcome = Outcome.PENDING
        elif action == Action.RETRY_LATER:
            outcome = Outcome.PENDING
        elif action == Action.NUDGE:
            outcome = Outcome.SIMULATED
        elif action == Action.ESCALATE_TO_HUMAN:
            outcome = Outcome.ESCALATED
        elif action == Action.STOP:
            outcome = Outcome.WITHHELD
        else:
            outcome = Outcome.PENDING

        return {
            "action": action,
            "outcome": outcome,
            "ladder_step": ladder_step,
            "rule_fired": rule_fired,
            "rationale": f"Deterministic action table: {rule_fired.value}",
            "cause_source": cause_source.value,
            "llm_calls_used": llm_calls_used,
        }

    # Stage 4
    action, ladder_step, rule_fired, rationale, llm_calls_used = await select_action_llm(
        event, cause, run_id, as_of, llm_calls_used, use_llm
    )

    if action == Action.RETRY_NOW:
        outcome = Outcome.PENDING
    elif action == Action.RETRY_LATER:
        outcome = Outcome.PENDING
    elif action == Action.NUDGE:
        outcome = Outcome.SIMULATED
    elif action == Action.ESCALATE_TO_HUMAN:
        outcome = Outcome.ESCALATED
    elif action == Action.STOP:
        outcome = Outcome.WITHHELD
    else:
        outcome = Outcome.PENDING

    return {
        "action": action,
        "outcome": outcome,
        "ladder_step": ladder_step,
        "rule_fired": rule_fired,
        "rationale": rationale,
        "cause_source": cause_source.value,
        "llm_calls_used": llm_calls_used,
    }