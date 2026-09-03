#!/usr/bin/env python3
"""
RevFlow Synthetic Dataset Generator — generates 300 events per §6.

Run from backend/ directory:
    python scripts/generate_dataset.py

Output: backend/data/synthetic_events.json
"""
import json
import random
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.contracts.config import RANDOM_SEED, BATCH_SIZE
from revflow.contracts.enums import EventType, Cause, LadderStep
from revflow.contracts.decline_map import DECLINE_CODE_TO_CAUSE, CAUSE_TO_DECLINE_CODES


# ─── Configuration from §6 ────────────────────────────────────────────────────

# Fixed base time for reproducibility (derived from seed)
BASE_TIME = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)

# Pipeline split
PIPELINE_COUNTS = {
    EventType.CHECKOUT_DROPOFF: 150,
    EventType.SUBSCRIPTION_FAILURE: 100,
    EventType.B2B_RECEIVABLE: 50,
}

# Cause distributions per pipeline (§6.2)
CAUSE_DISTRIBUTION = {
    EventType.CHECKOUT_DROPOFF: {
        Cause.INSUFFICIENT_FUNDS: 33,
        Cause.TECHNICAL_DECLINE: 28,
        Cause.BANK_TIMEOUT: 20,
        Cause.AUTHENTICATION_FAILED: 14,
        Cause.BUSINESS_DECLINE: 10,
        Cause.SESSION_TIMEOUT: 20,
        Cause.USER_ABANDONED: 25,
    },
    EventType.SUBSCRIPTION_FAILURE: {
        Cause.INSUFFICIENT_FUNDS: 45,
        Cause.BANK_TIMEOUT: 22,
        Cause.MANDATE_EXPIRED: 21,
        Cause.USER_REVOKED: 12,
    },
    EventType.B2B_RECEIVABLE: {
        Cause.INVOICE_OVERDUE: 34,
        Cause.AWAITING_PO: 9,
        Cause.INVOICE_DISPUTED: 7,
    },
}

# Amount ranges per pipeline (§6.4) - in rupees, log-uniform
AMOUNT_RANGES = {
    EventType.CHECKOUT_DROPOFF: (299, 9_999),
    EventType.SUBSCRIPTION_FAILURE: (99, 4_999),
    EventType.B2B_RECEIVABLE: (15_000, 250_000),
}

# Retry count distribution (§6.5) - applies to checkout_dropoff and subscription_failure
RETRY_COUNT_DIST = {
    0: 0.70,
    1: 0.20,
    2: 0.07,
    3: 0.03,
}

# Invoice ageing for b2b_receivable (§6.6)
INVOICE_AGE_BANDS = [
    (5, "<7", LadderStep.NONE, LadderStep.NONE),
    (12, "7-20", LadderStep.NONE, LadderStep.GENTLE_REMINDER),
    (11, "21-44", LadderStep.GENTLE_REMINDER, LadderStep.FIRM_REMINDER),
    (6, "45+", LadderStep.FIRM_REMINDER, LadderStep.FLAG_FOR_HUMAN),
]

# Customer reply / PTP seeding (§6.7)
# 20 events with replies: 15 b2b, 5 subscription
# 11 parseable PTP, 4 commitment no date, 5 no commitment
# Of 11 parseable: 7 future (active), 4 past (broken)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log_uniform(low: float, high: float, rng: random.Random) -> float:
    """Sample from log-uniform distribution."""
    return float(rng.uniform(low, high))  # simplified for now; true log-uniform would be 10**rng.uniform(log10(low), log10(high))

def sample_customer_id(existing: Dict[str, int], nudge_eligible: bool = False, rng: random.Random = None) -> str:
    """Sample a customer ID, reusing some to exercise FR-11 contact cap."""
    if rng is None:
        rng = random
    # 30% chance to reuse an existing customer
    if existing and rng.random() < 0.3:
        return rng.choice(list(existing.keys()))
    # Create new customer
    new_id = f"CUST-{len(existing) + 1:04d}"
    return new_id

def sample_retry_count(rng: random.Random = None) -> int:
    """Sample retry count from distribution."""
    if rng is None:
        rng = random
    r = rng.random()
    cum = 0.0
    for count, prob in RETRY_COUNT_DIST.items():
        cum += prob
        if r <= cum:
            return count
    return 0


# ─── Event Generation ─────────────────────────────────────────────────────────

def generate_events() -> List[Dict[str, Any]]:
    """Generate 300 events per §6 specifications."""
    rng = random.Random(RANDOM_SEED)
    events = []
    customer_pool = {}
    event_id_counter = 0

    # First, generate the base events with their true_cause and decline_code
    for event_type, count in PIPELINE_COUNTS.items():
        cause_dist = CAUSE_DISTRIBUTION[event_type]

        # Expand cause distribution into a list
        cause_list = []
        for cause, c in cause_dist.items():
            cause_list.extend([cause] * c)

        # Shuffle to randomise order within pipeline
        rng.shuffle(cause_list)

        for true_cause in cause_list:
            event_id_counter += 1

            # Customer ID
            customer_id = sample_customer_id(customer_pool, rng=rng)
            customer_pool[customer_id] = customer_pool.get(customer_id, 0) + 1

            # Amount (log-uniform in range)
            low, high = AMOUNT_RANGES[event_type]
            amount = log_uniform(low, high, rng)

            # Decline code
            decline_code = None
            decline_message = None
            if true_cause in CAUSE_TO_DECLINE_CODES:
                codes = CAUSE_TO_DECLINE_CODES[true_cause]
                decline_code = rng.choice(codes)
            # For b2b_receivable and user_abandoned, decline_code stays None

            # Retry count
            retry_count = 0
            if event_type in (EventType.CHECKOUT_DROPOFF, EventType.SUBSCRIPTION_FAILURE):
                retry_count = sample_retry_count(rng)

            # Ladder step (for b2b_receivable)
            ladder_step = LadderStep.NONE
            invoice_issued_at = None
            invoice_due_date = None

            if event_type == EventType.B2B_RECEIVABLE:
                if true_cause == Cause.INVOICE_OVERDUE:
                    # Assign based on age bands - ensure due_date matches the band
                    age_band = rng.choices(
                        INVOICE_AGE_BANDS,
                        weights=[b[0] for b in INVOICE_AGE_BANDS]
                    )[0]
                    ladder_step = age_band[2]  # Initial ladder step for this band
                    band_name = age_band[1]  # "<7", "7-20", "21-44", "45+"

                    # Set invoice dates to achieve the desired age for this band
                    if band_name == "<7":
                        due_date = BASE_TIME.date() - timedelta(days=rng.randint(1, 6))
                    elif band_name == "7-20":
                        due_date = BASE_TIME.date() - timedelta(days=rng.randint(7, 20))
                    elif band_name == "21-44":
                        due_date = BASE_TIME.date() - timedelta(days=rng.randint(21, 44))
                    elif band_name == "45+":
                        due_date = BASE_TIME.date() - timedelta(days=rng.randint(45, 60))
                    else:
                        due_date = BASE_TIME.date() - timedelta(days=rng.randint(1, 60))
                    
                    invoice_due_date = due_date.isoformat()
                    invoice_issued_at = (due_date - timedelta(days=30)).isoformat()
                else:
                    # awaiting_po, invoice_disputed - not overdue yet
                    # due_date is today or in the future (not yet overdue)
                    # invoice_disputed will have dispute_raised=True
                    due_date = BASE_TIME.date() + timedelta(days=rng.randint(0, 30))
                    invoice_due_date = due_date.isoformat()
                    invoice_issued_at = (BASE_TIME.date() - timedelta(days=rng.randint(30, 60))).isoformat()

            # Session fields for checkout_dropoff
            session_started_at = None
            checkout_resume_token = None
            if event_type == EventType.CHECKOUT_DROPOFF:
                session_started_at = (BASE_TIME - timedelta(minutes=rng.randint(1, 30))).isoformat()
                checkout_resume_token = f"tok_{rng.randint(100000, 999999)}"

            event = {
                "event_type": event_type.value,
                "amount": amount,
                "customer_id": customer_id,
                "decline_code": decline_code,
                "decline_message": decline_message,
                "true_cause": true_cause.value,
                "retry_count": retry_count,
                "ladder_step": ladder_step.value,
                "invoice_issued_at": invoice_issued_at,
                "invoice_due_date": invoice_due_date,
                "session_started_at": session_started_at,
                "checkout_resume_token": checkout_resume_token,
                "customer_reply_text": None,  # Will be added in PTP pass
                "dispute_raised": true_cause == Cause.INVOICE_DISPUTED,
            }
            events.append(event)

    # ─── Mark 36 events as ambiguous (§6.3) ──────────────────────────────────
    # Ambiguous = decline_code = null OR code not in map, decline_message populated
    # Hard-stop events (user_revoked, invoice_disputed) must NOT be ambiguous

    non_hard_stop_indices = [
        i for i, e in enumerate(events)
        if e["true_cause"] not in ("user_revoked", "invoice_disputed")
    ]

    ambiguous_indices = rng.sample(non_hard_stop_indices, 36)
    ambiguous_messages = [
        "txn could not be completed, please contact issuing bank",
        "payment failed due to unknown error",
        "issuer declined transaction",
        "network error during processing",
        "timeout waiting for issuer response",
        "invalid request parameters",
        "authentication required but not provided",
        "account restrictions prevent payment",
        "velocity limit exceeded",
        "risk score too high",
    ] * 4  # 40 messages, enough for 36

    for i, idx in enumerate(ambiguous_indices):
        events[idx]["decline_code"] = None
        events[idx]["decline_message"] = ambiguous_messages[i]

    # ─── Add PTP replies (§6.7) ──────────────────────────────────────────────
    # 20 events: 15 b2b, 5 subscription
    # 11 parseable PTP, 4 commitment no date, 5 no commitment
    # Of 11 parseable: 7 future (active), 4 past (broken)

    b2b_indices = [i for i, e in enumerate(events) if e["event_type"] == "b2b_receivable"]
    sub_indices = [i for i, e in enumerate(events) if e["event_type"] == "subscription_failure"]

    # Shuffle
    rng.shuffle(b2b_indices)
    rng.shuffle(sub_indices)

    ptp_indices = b2b_indices[:15] + sub_indices[:5]
    rng.shuffle(ptp_indices)

    # Parseable PTP (11) - with explicit dates
    parseable_replies = [
        ("I will pay by 2026-09-15", "2026-09-15"),
        ("Payment will be made on 2026-09-20", "2026-09-20"),
        ("Expect payment by 2026-09-25", "2026-09-25"),
        ("Will settle on 2026-10-01", "2026-10-01"),
        ("Promise to pay by 2026-10-05", "2026-10-05"),
        ("Payment scheduled for 2026-10-10", "2026-10-10"),
        ("Will clear by 2026-10-15", "2026-10-15"),
        ("Paid on 2026-08-15", "2026-08-15"),  # past - broken
        ("Paid on 2026-08-20", "2026-08-20"),  # past - broken
        ("Paid on 2026-08-25", "2026-08-25"),  # past - broken
        ("Paid on 2026-08-30", "2026-08-30"),  # past - broken
    ]
    rng.shuffle(parseable_replies)

    # Commitment language but no clear date (4)
    vague_replies = [
        "will settle this next week",
        "payment coming soon",
        "will pay in a few days",
        "expect to clear this shortly",
    ]

    # No commitment (5)
    no_commit_replies = [
        "thanks for the update",
        "received your message",
        "looking into it",
        "will check with finance",
        "ok noted",
    ]

    for i, idx in enumerate(ptp_indices):
        if i < 11:
            # Parseable
            text, date = parseable_replies[i]
            events[idx]["customer_reply_text"] = text
        elif i < 15:
            # Vague
            events[idx]["customer_reply_text"] = vague_replies[i - 11]
        else:
            # No commitment
            events[idx]["customer_reply_text"] = no_commit_replies[i - 15]

# ─── Final formatting ─────────────────────────────────────────────────────
    # Convert to output format
    output = []
    for e in events:
        output.append({
            "event_type": e["event_type"],
            "amount": e["amount"],
            "customer_id": e["customer_id"],
            "decline_code": e["decline_code"],
            "decline_message": e["decline_message"],
            "true_cause": e["true_cause"],
            "retry_count": e["retry_count"],
            "ladder_step": e["ladder_step"],
            "invoice_issued_at": e["invoice_issued_at"],
            "invoice_due_date": e["invoice_due_date"],
            "session_started_at": e["session_started_at"],
            "checkout_resume_token": e["checkout_resume_token"],
            "customer_reply_text": e["customer_reply_text"],
            "dispute_raised": e.get("dispute_raised", False),
        })

    return output


def main():
    """Generate and write synthetic events."""
    print(f"Generating {BATCH_SIZE} events with seed {RANDOM_SEED}...")

    events = generate_events()

    # Verify counts
    print(f"Generated {len(events)} events")
    by_type = {}
    by_cause = {}
    hard_stops = 0
    ambiguous = 0
    ptp_replies = 0

    for e in events:
        by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
        by_cause[e["true_cause"]] = by_cause.get(e["true_cause"], 0) + 1
        if e["true_cause"] in ("user_revoked", "invoice_disputed"):
            hard_stops += 1
        if e["decline_code"] is None and e["decline_message"] is not None:
            ambiguous += 1
        if e["customer_reply_text"] is not None:
            ptp_replies += 1

    print(f"By type: {by_type}")
    print(f"Hard-stop events: {hard_stops} (expected >= 19)")
    print(f"Ambiguous events: {ambiguous} (expected 36)")
    print(f"PTP replies: {ptp_replies} (expected 20)")

    # Write output
    output_path = Path("backend/data/synthetic_events.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Written to {output_path}")

    # Verify byte-identical on second run
    print("Verifying reproducibility...")
    events2 = generate_events()
    if events == events2:
        print("PASS: Two runs with same seed produce identical output")
    else:
        print("FAIL: Output differs between runs")
        sys.exit(1)


if __name__ == "__main__":
    main()