"""
RevFlow Classifier — Rules-based path.

Per §2.2: Classifier first attempts to resolve cause via decline_code lookup.
If decline_code is in DECLINE_CODE_TO_CAUSE map, return that cause (after applicability check).
If not, return None to signal LLM fallback is needed.

Applicability enforced per §2.2: a cause may only be assigned to event_types in its Applies-to column.
"""
from typing import Optional
from datetime import datetime, timezone

from revflow.contracts.enums import Cause, EventType, validate_cause_applicability
from revflow.contracts.decline_map import DECLINE_CODE_TO_CAUSE
from revflow.ingestion.normaliser import Event


def _parse_run_date(run_id: str) -> Optional[datetime]:
    """Parse run date from run_id format: RUN-YYYYMMDDTHHMMSS"""
    try:
        # RUN-YYYYMMDDTHHMMSS
        date_str = run_id.split('-')[1]  # YYYYMMDDTHHMMSS
        return datetime.strptime(date_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    except (ValueError, IndexError, AttributeError):
        return None


def _get_reference_time(event: Event) -> Optional[datetime]:
    """
    Get the reference time for age calculations.
    For synthetic data, use created_at if run_id timestamp is far in future.
    """
    run_dt = _parse_run_date(event.run_id)
    if run_dt is None:
        return None
    
    # If event has created_at, use it to detect synthetic data timestamp mismatch
    if event.created_at:
        try:
            created = datetime.fromisoformat(event.created_at.replace('Z', '+00:00'))
            # If run_dt is more than 1 hour after created_at, use created_at as reference
            # This handles synthetic data where run_id != event timestamp
            if (run_dt - created).total_seconds() > 3600:
                return created
        except (ValueError, AttributeError):
            pass
    
    return run_dt


def classify_by_rules(event: Event) -> Optional[Cause]:
    """
    Attempt to classify event cause using decline_code lookup table and deterministic B2B/checkout rules.

    Returns:
        Cause if decline_code maps to a valid, applicable cause, or B2B cause determined deterministically.
        None if decline_code is None/not in map, or mapped cause is not applicable, OR if event has
        a populated decline_message (intentional ambiguous event that must go to LLM).
    """
    # Intentional ambiguous events (populated decline_message) must go to LLM per §6.3
    if event.decline_message is not None and event.decline_message.strip():
        return None

    # First: try decline_code lookup for checkout/subscription events
    if event.decline_code is not None:
        cause = DECLINE_CODE_TO_CAUSE.get(event.decline_code)
        if cause is not None:
            # Enforce applicability per §2.2
            validated_cause = validate_cause_applicability(cause, event.event_type)
            if validated_cause != Cause.UNCLASSIFIED:
                return validated_cause
            # Mapped cause not applicable to this event_type → LLM fallback
            return None
        # Unknown decline_code → LLM fallback
        return None

    # No decline_code: try deterministic classification for B2B and checkout events
    if event.event_type == EventType.B2B_RECEIVABLE:
        return _classify_b2b_deterministic(event)

    if event.event_type == EventType.CHECKOUT_DROPOFF:
        return _classify_checkout_deterministic(event)

    # For subscription_failure with no decline_code, cannot classify deterministically
    return None


def _classify_b2b_deterministic(event: Event) -> Optional[Cause]:
    """
    Deterministically classify B2B events using invoice_age, ladder_step, and dispute_raised flag.
    Per §4.3: B2B actions determined by invoice_age, not decline_code.

    Key observable signals:
    - dispute_raised = True → invoice_disputed (hard stop)
    - invoice_age <= 0 (due_date >= run_date) → awaiting_po (not yet overdue)
    - invoice_age > 0 with ladder_step progression → invoice_overdue
    - invoice_age > 0 but ladder_step = "none" and age < 7 → invoice_overdue (early stage)
    - invoice_age <= 0 → awaiting_po (not yet overdue)
    """
    # invoice_disputed has explicit dispute_raised flag - this is a hard stop
    if event.dispute_raised:
        return Cause.INVOICE_DISPUTED

    # Compute invoice_age from reference time and invoice_due_date
    ref_dt = _get_reference_time(event)
    if event.invoice_due_date is not None and ref_dt is not None:
        try:
            due_date = datetime.fromisoformat(event.invoice_due_date.replace('Z', '+00:00')).date()
            ref_date = ref_dt.date()
            invoice_age = (ref_date - due_date).days
        except (ValueError, AttributeError):
            invoice_age = None
    else:
        invoice_age = None

    # invoice_disputed is a hard stop (handled above via dispute_raised)
    # awaiting_po: invoice not yet overdue (invoice_age <= 0)
    if invoice_age is not None and invoice_age <= 0:
        return Cause.AWAITING_PO

    # invoice_overdue: invoice_age > 0
    if invoice_age is not None and invoice_age > 0:
        # Age >= 7 with ladder progression → clear overdue
        if invoice_age >= 7 and event.ladder_step.value in ("gentle_reminder", "firm_reminder", "flag_for_human"):
            return Cause.INVOICE_OVERDUE
        # Age 1-6 days: early overdue, ladder_step still "none"
        if invoice_age < 7:
            return Cause.INVOICE_OVERDUE
        # Age >= 7 but ladder_step still "none" - early overdue, not yet escalated
        return Cause.INVOICE_OVERDUE

    # Unknown age - cannot classify deterministically
    return None


def _classify_checkout_deterministic(event: Event) -> Optional[Cause]:
    """
    Deterministically classify checkout events with no decline_code.
    session_timeout and user_abandoned have no decline_code by definition.
    
    Use session_started_at and reference timestamp to compute session age.
    CHECKOUT_SESSION_WINDOW_MINUTES = 15 per §4.1.
    """
    # Parse reference date (handles synthetic data timestamp mismatch)
    ref_dt = _get_reference_time(event)
    if ref_dt is None:
        return None
    
    if event.session_started_at is None:
        return None
    
    try:
        session_start = datetime.fromisoformat(event.session_started_at.replace('Z', '+00:00'))
        session_age_minutes = (ref_dt - session_start).total_seconds() / 60
    except (ValueError, AttributeError):
        return None
    
    # Session timeout: session older than 15 minutes with no payment attempt
    if session_age_minutes > 15:
        return Cause.SESSION_TIMEOUT
    
    # User abandoned: session started but not timed out, no payment attempt
    return Cause.USER_ABANDONED