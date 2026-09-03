"""
RevFlow Policy Engine — Stage 1: Hard Stop Check.

Per §4.2: Stage 1 executes before any LLM call. Deterministic, no I/O, short-circuits.

Hard stops: user_revoked, invoice_disputed (STOP_IF_CAUSE_IN).
If cause is in STOP_IF_CAUSE_IN → action=stop, outcome=withheld, rule_fired=hard_stop_cause_in_denylist.
"""
from typing import Optional

from revflow.contracts.config import STOP_IF_CAUSE_IN
from revflow.contracts.enums import Cause, Action, Outcome, RuleFired, LadderStep
from revflow.ingestion.normaliser import Event


def check_hard_stops(event: Event, cause: Cause) -> Optional[dict]:
    """
    Stage 1: Hard stop check.

    Args:
        event: The event being processed.
        cause: The classified cause (from rules or LLM).

    Returns:
        Decision dict if hard stop triggered, None otherwise.
        Decision dict contains: action, outcome, ladder_step, rule_fired, rationale.
    """
    if cause.value in STOP_IF_CAUSE_IN:
        # Hard stop triggered - no LLM call made
        if cause == Cause.USER_REVOKED:
            rationale = "Mandate revoked by user (user_revoked). No further action permitted."
        else:  # invoice_disputed
            rationale = "Invoice formally disputed (invoice_disputed). No further action permitted."

        return {
            "action": Action.STOP,
            "outcome": Outcome.WITHHELD,
            "ladder_step": LadderStep.NONE,
            "rule_fired": RuleFired.HARD_STOP_CAUSE_IN_DENYLIST,
            "rationale": rationale,
            "llm_calls_used": 0,
        }

    return None