"""
RevFlow Configuration Constants — generated from 00_CONTRACTS_RevFlow.md §4.1.

Single source of truth for all policy ceiling values.
Exposed read-only via GET /config. Not editable at runtime in Phase 0.
"""

# Retry policy
MAX_RETRIES: int = 3
COOLDOWN_HOURS: int = 24
RETRY_BACKOFF_HOURS: list[int] = [24, 48, 96]  # indexed by retry_count

# Checkout session
CHECKOUT_SESSION_WINDOW_MINUTES: int = 15

# Contact frequency cap
MAX_CONTACTS_PER_CUSTOMER_PER_DAY: int = 1

# Hard stops — exactly these two causes
STOP_IF_CAUSE_IN: list[str] = ["user_revoked", "invoice_disputed"]

# B2B Ladder thresholds (days past due)
LADDER_GENTLE_AFTER_DAYS: int = 7
LADDER_FIRM_AFTER_DAYS: int = 21
LADDER_FLAG_AFTER_DAYS: int = 45

# PTP grace period
PTP_GRACE_DAYS: int = 2

# LLM budget
LLM_CALL_BUDGET_PER_RUN: int = 90
LLM_MAX_ATTEMPTS: int = 3
LLM_TIMEOUT_SECONDS: int = 20

# Batch configuration
BATCH_SIZE: int = 300
RANDOM_SEED: int = 42

# Database
DATABASE_PATH: str = "backend/data/revflow.db"

# Performance budget
DECISION_LATENCY_BUDGET_MS: int = 5000

# All constants as a flat dict for GET /config
ALL_CONFIG = {
    "MAX_RETRIES": MAX_RETRIES,
    "COOLDOWN_HOURS": COOLDOWN_HOURS,
    "RETRY_BACKOFF_HOURS": RETRY_BACKOFF_HOURS,
    "CHECKOUT_SESSION_WINDOW_MINUTES": CHECKOUT_SESSION_WINDOW_MINUTES,
    "MAX_CONTACTS_PER_CUSTOMER_PER_DAY": MAX_CONTACTS_PER_CUSTOMER_PER_DAY,
    "STOP_IF_CAUSE_IN": STOP_IF_CAUSE_IN,
    "LADDER_GENTLE_AFTER_DAYS": LADDER_GENTLE_AFTER_DAYS,
    "LADDER_FIRM_AFTER_DAYS": LADDER_FIRM_AFTER_DAYS,
    "LADDER_FLAG_AFTER_DAYS": LADDER_FLAG_AFTER_DAYS,
    "PTP_GRACE_DAYS": PTP_GRACE_DAYS,
    "LLM_CALL_BUDGET_PER_RUN": LLM_CALL_BUDGET_PER_RUN,
    "LLM_MAX_ATTEMPTS": LLM_MAX_ATTEMPTS,
    "LLM_TIMEOUT_SECONDS": LLM_TIMEOUT_SECONDS,
    "BATCH_SIZE": BATCH_SIZE,
    "RANDOM_SEED": RANDOM_SEED,
    "DATABASE_PATH": DATABASE_PATH,
    "DECISION_LATENCY_BUDGET_MS": DECISION_LATENCY_BUDGET_MS,
}