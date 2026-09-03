"""
RevFlow Contract Enums — generated from 00_CONTRACTS_RevFlow.md §2.

This is the single source of truth for all closed enumerations.
frontend/lib/contracts.ts MUST mirror this file exactly.
TEST-12 asserts parity.
"""
from enum import StrEnum


class EventType(StrEnum):
    CHECKOUT_DROPOFF = "checkout_dropoff"
    SUBSCRIPTION_FAILURE = "subscription_failure"
    B2B_RECEIVABLE = "b2b_receivable"


class Cause(StrEnum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    BANK_TIMEOUT = "bank_timeout"
    TECHNICAL_DECLINE = "technical_decline"
    BUSINESS_DECLINE = "business_decline"
    AUTHENTICATION_FAILED = "authentication_failed"
    SESSION_TIMEOUT = "session_timeout"
    USER_ABANDONED = "user_abandoned"
    MANDATE_EXPIRED = "mandate_expired"
    USER_REVOKED = "user_revoked"
    INVOICE_OVERDUE = "invoice_overdue"
    INVOICE_DISPUTED = "invoice_disputed"
    AWAITING_PO = "awaiting_po"
    UNCLASSIFIED = "unclassified"


class Action(StrEnum):
    RETRY_NOW = "retry_now"
    RETRY_LATER = "retry_later"
    NUDGE = "nudge"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    STOP = "stop"


class LadderStep(StrEnum):
    NONE = "none"
    GENTLE_REMINDER = "gentle_reminder"
    FIRM_REMINDER = "firm_reminder"
    FLAG_FOR_HUMAN = "flag_for_human"


class Outcome(StrEnum):
    RECOVERED = "recovered"
    FAILED = "failed"
    API_ERROR = "api_error"
    SIMULATED = "simulated"
    PENDING = "pending"
    PAUSED = "paused"
    ESCALATED = "escalated"
    WITHHELD = "withheld"


class RuleFired(StrEnum):
    HARD_STOP_CAUSE_IN_DENYLIST = "hard_stop_cause_in_denylist"
    RETRY_CEILING_REACHED = "retry_ceiling_reached"
    PTP_PAUSE_ACTIVE = "ptp_pause_active"
    PTP_PROMISE_BROKEN_ESCALATED = "ptp_promise_broken_escalated"
    CONTACT_CAP_REACHED = "contact_cap_reached"
    COOLDOWN_ACTIVE = "cooldown_active"
    LADDER_NOT_YET_DUE = "ladder_not_yet_due"
    LADDER_STEP_BY_AGE = "ladder_step_by_age"
    DETERMINISTIC_ACTION_TABLE = "deterministic_action_table"
    LLM_REASONED_WITHIN_CEILING = "llm_reasoned_within_ceiling"
    LLM_OUTPUT_REJECTED_DEFAULTED = "llm_output_rejected_defaulted"


class CauseSource(StrEnum):
    RULE = "rule"
    LLM = "llm"


class SimulatedChannel(StrEnum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    VOICE_SCRIPT = "voice_script"


class Locale(StrEnum):
    EN = "en"
    HI = "hi"
    HINGLISH = "hinglish"


class PTPStatus(StrEnum):
    ACTIVE = "active"
    KEPT = "kept"
    BROKEN = "broken"


class BatchRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Applicability matrix: which causes apply to which event types
# From 00_CONTRACTS_RevFlow.md §2.2
CAUSE_APPLICABILITY: dict[Cause, set[EventType]] = {
    Cause.INSUFFICIENT_FUNDS: {EventType.CHECKOUT_DROPOFF, EventType.SUBSCRIPTION_FAILURE},
    Cause.BANK_TIMEOUT: {EventType.CHECKOUT_DROPOFF, EventType.SUBSCRIPTION_FAILURE},
    Cause.TECHNICAL_DECLINE: {EventType.CHECKOUT_DROPOFF, EventType.SUBSCRIPTION_FAILURE},
    Cause.BUSINESS_DECLINE: {EventType.CHECKOUT_DROPOFF},
    Cause.AUTHENTICATION_FAILED: {EventType.CHECKOUT_DROPOFF},
    Cause.SESSION_TIMEOUT: {EventType.CHECKOUT_DROPOFF},
    Cause.USER_ABANDONED: {EventType.CHECKOUT_DROPOFF},
    Cause.MANDATE_EXPIRED: {EventType.SUBSCRIPTION_FAILURE},
    Cause.USER_REVOKED: {EventType.SUBSCRIPTION_FAILURE},
    Cause.INVOICE_OVERDUE: {EventType.B2B_RECEIVABLE},
    Cause.INVOICE_DISPUTED: {EventType.B2B_RECEIVABLE},
    Cause.AWAITING_PO: {EventType.B2B_RECEIVABLE},
    Cause.UNCLASSIFIED: {EventType.CHECKOUT_DROPOFF, EventType.SUBSCRIPTION_FAILURE, EventType.B2B_RECEIVABLE},
}

# Hard-stop causes — exactly these two, matching SRS §3.1.1
STOP_IF_CAUSE_IN = {Cause.USER_REVOKED, Cause.INVOICE_DISPUTED}

# Valid action/outcome pairings — from contracts §2.5
VALID_ACTION_OUTCOME: dict[Action, set[Outcome]] = {
    Action.RETRY_NOW: {Outcome.RECOVERED, Outcome.FAILED, Outcome.API_ERROR},
    Action.RETRY_LATER: {Outcome.PENDING, Outcome.PAUSED},
    Action.NUDGE: {Outcome.SIMULATED},
    Action.ESCALATE_TO_HUMAN: {Outcome.ESCALATED},
    Action.STOP: {Outcome.WITHHELD},
}

# Valid ladder_step/action pairings — contracts §2.4
VALID_LADDER_ACTION: dict[LadderStep, set[Action]] = {
    LadderStep.NONE: {Action.RETRY_NOW, Action.RETRY_LATER, Action.NUDGE, Action.ESCALATE_TO_HUMAN, Action.STOP},
    LadderStep.GENTLE_REMINDER: {Action.NUDGE, Action.ESCALATE_TO_HUMAN},
    LadderStep.FIRM_REMINDER: {Action.NUDGE, Action.ESCALATE_TO_HUMAN},
    LadderStep.FLAG_FOR_HUMAN: {Action.ESCALATE_TO_HUMAN},
}


def validate_cause_applicability(cause: Cause, event_type: EventType) -> Cause:
    """Enforce applicability — reject out-of-scope causes, return unclassified."""
    if event_type in CAUSE_APPLICABILITY.get(cause, set()):
        return cause
    return Cause.UNCLASSIFIED


def validate_action_outcome(action: Action, outcome: Outcome) -> bool:
    """Check if action/outcome pairing is valid per contracts §2.5."""
    return outcome in VALID_ACTION_OUTCOME.get(action, set())


def validate_ladder_action(ladder_step: LadderStep, action: Action) -> bool:
    """Check if ladder_step/action pairing is valid per contracts §2.4."""
    return action in VALID_LADDER_ACTION.get(ladder_step, set())