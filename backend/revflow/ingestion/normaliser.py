"""
RevFlow Event Normaliser — converts raw input (synthetic or webhook) to canonical Event.

Per §3.2 and §7.10: both batch loader and webhook normalise to the same Event shape.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid

from revflow.contracts.enums import EventType, Cause, LadderStep


@dataclass
class Event:
    """Canonical event shape used throughout the pipeline."""
    event_id: str
    run_id: str
    event_type: EventType
    amount_inr: int  # Paise
    currency: str = "INR"
    customer_id: str = ""
    decline_code: Optional[str] = None
    decline_message: Optional[str] = None
    true_cause: Optional[str] = None  # Synthetic only, never read by classifier/policy
    retry_count: int = 0
    last_attempt_at: Optional[str] = None
    paused_until: Optional[str] = None
    ladder_step: LadderStep = LadderStep.NONE
    invoice_issued_at: Optional[str] = None
    invoice_due_date: Optional[str] = None
    session_started_at: Optional[str] = None
    checkout_resume_token: Optional[str] = None
    customer_reply_text: Optional[str] = None
    dispute_raised: bool = False  # Explicit dispute signal for B2B invoices
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Convert to dict for database insertion."""
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "event_type": self.event_type.value,
            "amount_inr": self.amount_inr,
            "currency": self.currency,
            "customer_id": self.customer_id,
            "decline_code": self.decline_code,
            "decline_message": self.decline_message,
            "true_cause": self.true_cause,
            "retry_count": self.retry_count,
            "last_attempt_at": self.last_attempt_at,
            "paused_until": self.paused_until,
            "ladder_step": self.ladder_step.value,
            "invoice_issued_at": self.invoice_issued_at,
            "invoice_due_date": self.invoice_due_date,
            "session_started_at": self.session_started_at,
            "checkout_resume_token": self.checkout_resume_token,
            "customer_reply_text": self.customer_reply_text,
            "created_at": self.created_at,
        }


def normalise_event(raw: dict, run_id: str, event_id: str) -> Event:
    """
    Normalise a raw event (from synthetic JSON or Razorpay webhook) to canonical Event.

    Args:
        raw: Raw event dict with keys like 'event_type', 'amount', 'customer_id', etc.
        run_id: The batch run ID this event belongs to.
        event_id: The event ID (EVT-XXXX).

    Returns:
        Canonical Event object.
    """
    # Parse event_type
    event_type_str = raw.get("event_type", "checkout_dropoff")
    try:
        event_type = EventType(event_type_str)
    except ValueError:
        event_type = EventType.CHECKOUT_DROPOFF

    # Amount in paise
    amount_rupees = raw.get("amount", 0)
    if isinstance(amount_rupees, str):
        amount_rupees = float(amount_rupees)
    amount_inr = int(round(amount_rupees * 100))

    # Customer ID
    customer_id = raw.get("customer_id", f"CUST-{uuid.uuid4().hex[:4].upper()}")

    # Decline code and message
    decline_code = raw.get("decline_code")
    decline_message = raw.get("decline_message")

    # True cause (synthetic only)
    true_cause = raw.get("true_cause")

    # Retry count
    retry_count = raw.get("retry_count", 0)

    # Ladder step
    ladder_step_str = raw.get("ladder_step", "none")
    try:
        ladder_step = LadderStep(ladder_step_str)
    except ValueError:
        ladder_step = LadderStep.NONE

    # Invoice fields
    invoice_issued_at = raw.get("invoice_issued_at")
    invoice_due_date = raw.get("invoice_due_date")

    # Session fields
    session_started_at = raw.get("session_started_at")
    checkout_resume_token = raw.get("checkout_resume_token")

    # Customer reply text (for PTP)
    customer_reply_text = raw.get("customer_reply_text")

    # Dispute raised flag (for B2B invoice_disputed)
    dispute_raised = raw.get("dispute_raised", False)

    # Created at
    created_at = raw.get("created_at", datetime.now(timezone.utc).isoformat())

    return Event(
        event_id=event_id,
        run_id=run_id,
        event_type=event_type,
        amount_inr=amount_inr,
        currency="INR",
        customer_id=customer_id,
        decline_code=decline_code,
        decline_message=decline_message,
        true_cause=true_cause,
        retry_count=retry_count,
        ladder_step=ladder_step,
        invoice_issued_at=invoice_issued_at,
        invoice_due_date=invoice_due_date,
        session_started_at=session_started_at,
        checkout_resume_token=checkout_resume_token,
        customer_reply_text=customer_reply_text,
        dispute_raised=dispute_raised,
        created_at=created_at,
    )