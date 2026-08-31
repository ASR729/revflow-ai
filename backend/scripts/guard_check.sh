#!/usr/bin/env bash
# RevFlow guard checks — four silent-failure classes.
# Run before every commit.  On Windows without bash, run the git grep lines directly
# in PowerShell; `git grep` ships with Git for Windows.
set -uo pipefail
fail=0
note() { printf '  %s\n' "$1"; }

echo "== 1. Prohibited messaging packages (TEST-13, FR-24, NFR-5) =="
# Absence is enforced, not documented.  docs/ is exempt: the specs name these
# packages in order to prohibit them.
if git grep -n -i -E '\b(twilio|plivo|exotel|gupshup|msg91|karix|sendgrid|mailgun|smtplib|boto3)\b' \
     -- . ':(exclude)docs' ':(exclude)scripts/guard_check.sh' ; then
  note "FAIL — a prohibited messaging dependency is present"; fail=1
else
  note "PASS — none present outside docs/"
fi

echo "== 2. Razorpay test mode only (contracts 00 section 8.3, rule 6) =="
if [ -f .env ]; then
  if grep -qE '^RAZORPAY_KEY_ID=rzp_test_' .env; then
    note "PASS — key id carries the rzp_test_ prefix"
  else
    note "FAIL — RAZORPAY_KEY_ID is absent or not a test key"; fail=1
  fi
else
  note "SKIP — no .env in this checkout"
fi

echo "== 3. .env never committed (DEP-3, NFR-4) =="
if [ -n "$(git log --all --full-history -- '**/.env' 2>/dev/null)" ]; then
  note "FAIL — .env appears in git history; this requires history rewriting"; fail=1
else
  note "PASS — no .env in any commit"
fi

echo "== 4. Hardcoded contract values outside contracts/ (NFR-7, rule 4) =="
# Values that belong to doc 00 must be imported, never written inline.  This is a
# heuristic scan: review each hit, do not assume every one is a defect.
if git grep -n -E '(MAX_RETRIES|COOLDOWN_HOURS|BATCH_SIZE|RANDOM_SEED|LLM_CALL_BUDGET_PER_RUN|PTP_GRACE_DAYS)[[:space:]]*=[[:space:]]*[0-9]' \
     -- backend ':(exclude)backend/revflow/contracts' ; then
  note "REVIEW — a contract constant is assigned outside contracts/"; fail=1
else
  note "PASS — no constant reassigned outside contracts/"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "ALL GUARD CHECKS PASS"
else
  echo "GUARD CHECKS FAILED — do not commit until resolved"
fi
exit "$fail"
