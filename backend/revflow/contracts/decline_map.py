"""
RevFlow Decline Code → Cause Mapping — from 00_CONTRACTS_RevFlow.md §8.2.

Synthetic codes prefixed with SYN_ so no reader mistakes them for production codes.
Generator and map are written together from the same constant list so they cannot drift.

Any decline_code not in this map routes to the LLM classifier (unclassified → Stage 4).
Do NOT populate with real NPCI/Razorpay codes from memory — only synthetic codes used by generate_dataset.py.
"""

from revflow.contracts.enums import Cause

# Synthetic decline codes → cause mapping
# Used by both generate_dataset.py and classifier/rules.py
DECLINE_CODE_TO_CAUSE: dict[str, Cause] = {
    # Checkout drop-off payment failures
    "SYN_INSUFFICIENT_FUNDS": Cause.INSUFFICIENT_FUNDS,
    "SYN_BANK_TIMEOUT": Cause.BANK_TIMEOUT,
    "SYN_TECHNICAL_DECLINE": Cause.TECHNICAL_DECLINE,
    "SYN_BUSINESS_DECLINE": Cause.BUSINESS_DECLINE,
    "SYN_AUTHENTICATION_FAILED": Cause.AUTHENTICATION_FAILED,

    # Subscription failures
    "SYN_MANDATE_EXPIRED": Cause.MANDATE_EXPIRED,
    "SYN_USER_REVOKED": Cause.USER_REVOKED,

    # B2B receivables — these don't use decline codes, but included for completeness
    # invoice_overdue, invoice_disputed, awaiting_po are determined by other fields
}

# Reverse mapping for generator
CAUSE_TO_DECLINE_CODES: dict[Cause, list[str]] = {}
for code, cause in DECLINE_CODE_TO_CAUSE.items():
    CAUSE_TO_DECLINE_CODES.setdefault(cause, []).append(code)

# Codes that map to each cause (for ambiguous subset generation)
# Ambiguous events have decline_code = null or a code NOT in this map
ALL_KNOWN_DECLINE_CODES = set(DECLINE_CODE_TO_CAUSE.keys())