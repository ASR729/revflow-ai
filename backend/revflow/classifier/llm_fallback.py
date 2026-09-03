"""
RevFlow Classifier — LLM fallback path.

Per §2.2 and §4.2 Stage 4: For ambiguous events (decline_code not in map),
the LLM classifier is invoked with the allowed causes for the event_type.

The LLM adapter is called via the provider-agnostic interface in adapters/llm.py.
"""
from typing import Optional, List

from revflow.contracts.enums import Cause, EventType, CAUSE_APPLICABILITY, validate_cause_applicability
from revflow.contracts.decline_map import DECLINE_CODE_TO_CAUSE
from revflow.adapters.llm import get_llm_adapter
from revflow.ingestion.normaliser import Event


def get_allowed_causes(event_type: EventType) -> List[Cause]:
    """Get causes applicable to the given event_type per §2.2."""
    allowed = []
    for cause, applies_to in CAUSE_APPLICABILITY.items():
        if event_type in applies_to:
            allowed.append(cause)
    return allowed


async def classify_by_llm(event: Event) -> Cause:
    """
    Classify cause using LLM for ambiguous events.

    Args:
        event: Event with decline_code=None or unknown, and decline_message populated.

    Returns:
        Cause from the allowed set for this event_type.
        Falls back to Cause.UNCLASSIFIED if LLM fails or returns invalid cause.
    """
    # Only call LLM for truly ambiguous events (decline_code None/unmapped AND populated message)
    if event.decline_code is not None and event.decline_code in DECLINE_CODE_TO_CAUSE:
        # This should have been handled by rules - shouldn't reach LLM
        pass

    # Only call LLM for events with populated decline_message (intentional ambiguous)
    if event.decline_message is None or event.decline_message.strip() == "":
        # No message = not intentionally ambiguous, don't call LLM
        return Cause.UNCLASSIFIED

    # Get allowed causes for this event_type
    allowed_causes = get_allowed_causes(event.event_type)
    allowed_cause_values = [c.value for c in allowed_causes]

    # Get LLM adapter
    adapter = get_llm_adapter()

    # Call LLM to classify cause
    result = await adapter.classify_cause(event, allowed_cause_values)

    if result is None:
        # LLM unavailable, timeout, or budget exceeded
        return Cause.UNCLASSIFIED

    cause_str, confidence = result

    # Validate returned cause is in allowed set
    try:
        cause = Cause(cause_str)
    except ValueError:
        return Cause.UNCLASSIFIED

    # Enforce applicability (should already be guaranteed by allowed_causes)
    validated = validate_cause_applicability(cause, event.event_type)
    if validated == Cause.UNCLASSIFIED:
        return Cause.UNCLASSIFIED

    return cause