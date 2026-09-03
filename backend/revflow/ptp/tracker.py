"""
RevFlow PTP Tracker — Promise-to-Pay detection and handling.

Per §4.4:
1. Detect: regex pass for explicit dates, LLM fallback for commitment language
2. Pause: insert ptp_commitments, set paused_until, action=retry_later, outcome=paused
3. Hold: while run_date <= promised_date + PTP_GRACE_DAYS → retry_later/paused
4. Resume: past grace period → status=broken, advance one step above ladder_step_at_pause
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from revflow.contracts.config import PTP_GRACE_DAYS
from revflow.contracts.enums import CauseSource, PTPStatus, LadderStep
from revflow.adapters.llm import get_llm_adapter
from revflow.ingestion.normaliser import Event
from revflow.db.connection import get_connection


# Regex patterns for explicit date extraction
DATE_PATTERNS = [
    r"by\s+(\d{4}-\d{2}-\d{2})",
    r"on\s+(\d{4}-\d{2}-\d{2})",
    r"pay\s+(?:by|on)\s+(\d{4}-\d{2}-\d{2})",
    r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
    r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})",
]


def extract_date_regex(text: str) -> Optional[str]:
    """
    Extract date from text using regex patterns.
    Returns ISO date string (YYYY-MM-DD) or None.
    """
    text_lower = text.lower()

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                # YYYY-MM-DD format
                return groups[0]
            elif len(groups) == 3:
                # DD/MM/YYYY or DD-MMM-YYYY
                try:
                    if groups[1].isalpha():
                        # Month name format
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        day = int(groups[0])
                        month = month_map.get(groups[1][:3].lower(), 1)
                        year = int(groups[2])
                    else:
                        # DD/MM/YYYY
                        day = int(groups[0])
                        month = int(groups[1])
                        year = int(groups[2])
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, KeyError):
                    continue

    return None


async def detect_ptp(event: Event) -> Tuple[Optional[str], Optional[CauseSource]]:
    """
    Detect PTP from customer_reply_text.

    Returns:
        (promised_date, detection_source) or (None, None) if no PTP detected.
        detection_source is 'rule' (regex) or 'llm'.
    """
    if not event.customer_reply_text:
        return None, None

    # 1. Regex pass for explicit dates
    promised_date = extract_date_regex(event.customer_reply_text)
    if promised_date:
        return promised_date, CauseSource.RULE

    # 2. LLM fallback for commitment language without clear date
    # Check if text contains commitment language
    commitment_keywords = [
        "will pay", "will settle", "payment coming", "expect to pay",
        "promise to pay", "pay soon", "clear this", "next week",
        "in a few days", "shortly"
    ]
    text_lower = event.customer_reply_text.lower()
    has_commitment = any(kw in text_lower for kw in commitment_keywords)

    if has_commitment:
        adapter = get_llm_adapter()
        extracted = await adapter.extract_ptp_date(event.customer_reply_text)
        if extracted:
            return extracted, CauseSource.LLM

    return None, None


def handle_ptp_pause(
    event: Event,
    promised_date: str,
    detection_source: CauseSource,
    run_id: str,
    run_date: datetime
) -> dict:
    """
    Handle PTP pause: insert commitment, set event paused_until, decide action.

    Returns decision dict for policy engine.
    """
    from revflow.contracts.enums import Action, Outcome, RuleFired
    from revflow.db.ledger import insert_audit_row

    with get_connection() as conn:
        # Insert ptp_commitments row
        conn.execute(
            """INSERT INTO ptp_commitments (
                run_id, event_id, promised_date, detected_from_text,
                detection_source, status, ladder_step_at_pause, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                event.event_id,
                promised_date,
                event.customer_reply_text[:500],  # Truncate for storage
                detection_source.value,
                PTPStatus.ACTIVE.value,
                event.ladder_step,
                datetime.now(timezone.utc).isoformat(),
            )
        )

        # Update event paused_until
        conn.execute(
            "UPDATE events SET paused_until = ? WHERE event_id = ?",
            (promised_date, event.event_id)
        )

    # Audit log for pause
    insert_audit_row(
        run_id=run_id,
        event_id=event.event_id,
        event_type=event.event_type.value,
        cause="unclassified",  # PTP pause is independent of cause
        cause_source=detection_source.value,
        rule_fired=RuleFired.PTP_PAUSE_ACTIVE.value,
        action=Action.RETRY_LATER.value,
        ladder_step=event.ladder_step,
        rationale=f"PTP detected via {detection_source.value}: promised payment by {promised_date}",
        outcome=Outcome.PAUSED.value,
        amount_inr=event.amount_inr,
        is_simulated=0,
        llm_calls_used=0,
    )

    return {
        "action": Action.RETRY_LATER,
        "outcome": Outcome.PAUSED,
        "ladder_step": event.ladder_step,
        "rule_fired": RuleFired.PTP_PAUSE_ACTIVE,
        "rationale": f"PTP detected via {detection_source.value}: promised payment by {promised_date}",
        "llm_calls_used": 0,
    }


def check_ptp_status(event: Event, run_date: datetime) -> Optional[dict]:
    """
    Check PTP status for an event at run time.

    Returns:
        Decision dict if PTP is active or broken, None otherwise.
    """
    with get_connection() as conn:
        ptp = conn.execute(
            "SELECT promised_date, status, ladder_step_at_pause FROM ptp_commitments "
            "WHERE event_id = ? AND status IN ('active', 'broken') ORDER BY created_at DESC LIMIT 1",
            (event.event_id,)
        ).fetchone()

    if not ptp:
        return None

    promised_date = datetime.fromisoformat(ptp["promised_date"]).replace(tzinfo=timezone.utc)
    status = PTPStatus(ptp["status"])
    ladder_step_at_pause = LadderStep(ptp["ladder_step_at_pause"])
    grace_end = promised_date + timedelta(days=PTP_GRACE_DAYS)

    if status == PTPStatus.ACTIVE:
        if run_date <= grace_end:
            # Still in grace period
            return {
                "action": Action.RETRY_LATER,
                "outcome": Outcome.PAUSED,
                "ladder_step": LadderStep(event.ladder_step),
                "rule_fired": RuleFired.PTP_PAUSE_ACTIVE,
                "rationale": f"PTP active until {promised_date.date()} + {PTP_GRACE_DAYS} days grace",
                "llm_calls_used": 0,
            }
        else:
            # Grace period expired - promise broken
            return _handle_broken_promise(event, ladder_step_at_pause, promised_date)

    elif status == PTPStatus.BROKEN:
        # Already processed as broken
        return None

    return None


def _handle_broken_promise(
    event: Event,
    ladder_step_at_pause: LadderStep,
    promised_date: datetime
) -> dict:
    """Handle broken promise - advance one step above ladder_step_at_pause."""
    from revflow.contracts.enums import Action, Outcome, RuleFired
    from revflow.policy.guards import _advance_ladder_step

    next_step = _advance_ladder_step(ladder_step_at_pause)

    return {
        "action": Action.ESCALATE_TO_HUMAN,
        "outcome": Outcome.ESCALATED,
        "ladder_step": next_step,
        "rule_fired": RuleFired.PTP_PROMISE_BROKEN_ESCALATED,
        "rationale": f"PTP broken (promised {promised_date.date()}, grace ended). "
                     f"Resumed one step above {ladder_step_at_pause.value} → {next_step.value}",
        "llm_calls_used": 0,
    }


from revflow.contracts.enums import Action, Outcome, RuleFired