"""
RevFlow Batch Loader — loads synthetic events from JSON into the database.

Per §6: generate_dataset.py produces synthetic_events.json, this loads it.
"""
import json
from pathlib import Path
from typing import List

from revflow.db.connection import get_connection
from revflow.ingestion.normaliser import normalise_event, Event


SYNTHETIC_EVENTS_PATH = Path("backend/data/synthetic_events.json")


def load_synthetic_events(run_id: str, regenerate: bool = False) -> List[Event]:
    """
    Load synthetic events from JSON file.

    Args:
        run_id: The batch run ID to associate events with.
        regenerate: If True, ignore existing file (caller should regenerate first).

    Returns:
        List of canonical Event objects.
    """
    if not SYNTHETIC_EVENTS_PATH.exists():
        raise FileNotFoundError(
            f"Synthetic events not found at {SYNTHETIC_EVENTS_PATH}. "
            "Run generate_dataset.py first."
        )

    with open(SYNTHETIC_EVENTS_PATH, "r") as f:
        raw_events = json.load(f)

    events = []
    for i, raw in enumerate(raw_events):
        event_id = f"EVT-{i+1:04d}"
        event = normalise_event(raw, run_id, event_id)
        events.append(event)

    return events


def insert_events(events: List[Event]) -> int:
    """
    Insert events into the database.

    Args:
        events: List of Event objects to insert.

    Returns:
        Number of events inserted.
    """
    with get_connection() as conn:
        for event in events:
            conn.execute(
                """
                INSERT INTO events (
                    event_id, run_id, event_type, amount_inr, currency, customer_id,
                    decline_code, decline_message, true_cause, retry_count,
                    last_attempt_at, paused_until, ladder_step,
                    invoice_issued_at, invoice_due_date, session_started_at,
                    checkout_resume_token, customer_reply_text, dispute_raised, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.event_type.value,
                    event.amount_inr,
                    event.currency,
                    event.customer_id,
                    event.decline_code,
                    event.decline_message,
                    event.true_cause,
                    event.retry_count,
                    event.last_attempt_at,
                    event.paused_until,
                    event.ladder_step.value,
                    event.invoice_issued_at,
                    event.invoice_due_date,
                    event.session_started_at,
                    event.checkout_resume_token,
                    event.customer_reply_text,
                    int(event.dispute_raised),
                    event.created_at,
                ),
            )
    return len(events)