# 00 — Binding Technical Contracts

**Product:** RevFlow — AI-Powered Revenue Recovery Orchestration
**Track:** 03 — AI Revenue Recovery (Razorpay AI Buildathon)
**Document version:** 1.0
**Status:** BINDING. This document overrides all others on any conflict.

---

## 0. How to use this document set

### 0.1 The complete document set

There are exactly nine documents. No other document exists. If any document
references a filename not on this list, that reference is a defect — report it,
do not invent the file.

| # | File | Role |
|---|---|---|
| 00 | `00_CONTRACTS_RevFlow.md` | **This file.** Binding enums, schemas, formulas, APIs, config. |
| 01 | `01_PRD_RevFlow.md` | Product requirements: problem, personas, features, user stories, metrics. |
| 02 | `02_Teardown_RevFlow.md` | Competitive gap analysis; justifies the product. |
| 03 | `03_Roadmap_RevFlow.md` | Buildathon delivery sequence and milestones. |
| 04 | `04_SRS_RevFlow.md` | Functional (FR-*) and non-functional (NFR-*) requirements. |
| 05 | `05_System_Architecture_RevFlow.md` | Components, data flow, technology decisions. |
| 06 | `06_UIUX_RevFlow.md` | Design tokens, screens, components, states. |
| 07 | `07_Development_Plan_RevFlow.md` | Task-level engineering plan, dependencies, DoD. |
| 08 | `08_Audit_Report_RevFlow.md` | Record of defects found in the v1 document set and their resolutions. Not a build input. |

### 0.2 Reading order for an implementing agent

Read `00` (this file) first and completely. Then `04_SRS` for requirement IDs,
then `05_System_Architecture` for structure, then `07_Development_Plan` for task
order, then `06_UIUX` when you reach frontend work. Read `01_PRD` and
`02_Teardown` for intent and framing. `03_Roadmap` sequences milestones.

### 0.3 Precedence rules (resolve conflicts in this order)

1. **`00_CONTRACTS_RevFlow.md` (this file)** — enums, schemas, formulas, API
   shapes, config values, file layout.
2. **`04_SRS_RevFlow.md`** — what the system must do (FR/NFR IDs).
3. **`05_System_Architecture_RevFlow.md`** — how it is structured.
4. **`06_UIUX_RevFlow.md`** — how the frontend looks and behaves.
5. **`07_Development_Plan_RevFlow.md`** — task order and Definition of Done.
6. **`01_PRD_RevFlow.md` / `02_Teardown_RevFlow.md` / `03_Roadmap_RevFlow.md`** — intent, scope, sequencing.

### 0.4 Anti-hallucination rules (non-negotiable)

These rules exist because an implementing agent that guesses will produce a
build that looks complete and is silently wrong.

1. **Never invent an enum value.** Every `cause`, `action`, `outcome`,
   `rule_fired`, and `ladder_step` value MUST come from Section 2 of this
   document. If a case arises that no enum value covers, use the designated
   fallback (`unclassified` cause, `escalate_to_human` action) and log it —
   do not add a new value.
2. **Never invent a database column.** The schemas in Section 3 are complete.
   If you need a field that does not exist, that is a specification gap: stop
   and surface it rather than adding a column.
3. **Never invent an external API endpoint path.** Specifically: do not guess
   Razorpay endpoint URLs. Implement only against endpoints you have verified
   in official Razorpay documentation. If an endpoint cannot be verified, the
   adapter MUST return outcome `api_error` with a clear message — see
   Section 8.3.
4. **Never invent a metric.** Every number the dashboard displays must be
   computed by a formula defined in Section 5 from rows that exist in the
   database. No hardcoded values, no placeholder numbers shipped as real.
5. **Wireframe numbers are illustrative, not targets.** Every rupee figure and
   percentage in `06_UIUX_RevFlow.md` is layout filler. Do not hardcode them.
   Do not treat them as acceptance thresholds.
6. **Test mode only.** `RAZORPAY_KEY_ID` MUST match `^rzp_test_`. Assert this at
   startup and refuse to boot otherwise. See Section 8.3.
7. **No messaging provider.** No SMS, WhatsApp, voice, or email client library
   may appear in `requirements.txt`, `package.json`, or anywhere in the source
   tree. See Section 8.4.

---

## 1. Canonical vocabulary

Three words in this project are dangerously overloaded. Use them only as
defined here.

| Term | Means exactly | Does NOT mean |
|---|---|---|
| **Pipeline** | One of the three `event_type` values: `checkout_dropoff`, `subscription_failure`, `b2b_receivable`. This is the dimension metrics are broken out by. | A product feature. |
| **Module** | One of the six product features listed in `01_PRD_RevFlow.md` Section 5. A grouping for scope and roadmap purposes only. | A metrics dimension. Never a JSON key. |
| **Component** | One of the six runtime components in `05_System_Architecture_RevFlow.md` Section 3, each a Python package. | Either of the above. |

The dashboard metric is **recovery by pipeline**, keyed by `event_type`. It is
never keyed by module or component.

### 1.1 Module ↔ pipeline ↔ component map

| Module (PRD §5) | SRS section | Primary component | Pipelines touched |
|---|---|---|---|
| 1. Root Cause Classification | 04 §3.1 | `classifier` | all three |
| 2. Bounded Policy Engine | 04 §3.1.1 | `policy` | all three |
| 3. Recovery Execution | 04 §3.2, §3.3, §3.6 | `executor` | all three |
| 4. Promise-to-Pay Tracking | 04 §3.5 | `ptp` | `subscription_failure`, `b2b_receivable` |
| 5. B2B Receivables Ladder | 04 §3.4 | `ladder` | `b2b_receivable` |
| 6. Audit Ledger + Dashboard | 04 §3.7 | `ledger`, `api` | all three |

Hinglish voice generation (SRS §3.6) is part of Module 3, not a seventh module.

---

## 2. Closed enumerations

Every enum below is **closed**. Implement each as a Python `enum.StrEnum` in
`backend/revflow/contracts/enums.py` and as a TypeScript union in
`frontend/lib/contracts.ts`. Both files are generated from this section and MUST
agree.

### 2.1 `event_type` — 3 values

| Value | Meaning |
|---|---|
| `checkout_dropoff` | A checkout session that ended without a successful payment. |
| `subscription_failure` | A recurring charge on a mandate that failed. |
| `b2b_receivable` | An issued invoice that is unpaid past its due date. |

### 2.2 `cause` — 13 values

`cause` is assigned by the Root Cause Classifier. Applicability is enforced: a
cause may only be assigned to an event whose type appears in its Applies-to
column. A cause assigned outside its applicability is rejected and replaced with
`unclassified`.

| Value | Applies to | NPCI family | Meaning |
|---|---|---|---|
| `insufficient_funds` | checkout, subscription | Business Decline | Payer account lacked balance. |
| `bank_timeout` | checkout, subscription | Technical Decline | Issuer or rail did not respond in time. |
| `technical_decline` | checkout, subscription | Technical Decline | Rail/issuer technical failure, not payer-caused. |
| `business_decline` | checkout | Business Decline | Issuer declined on policy grounds (limit, block). |
| `authentication_failed` | checkout | — | 3DS / OTP / UPI PIN not completed successfully. |
| `session_timeout` | checkout | — | Checkout session expired before any payment attempt. |
| `user_abandoned` | checkout | — | Session left deliberately, no payment attempt, no failure. |
| `mandate_expired` | subscription | — | Mandate is past its validity window; re-authorisation required. |
| `user_revoked` | subscription | — | Payer actively cancelled the mandate. **STOP cause.** |
| `invoice_overdue` | b2b | — | Invoice unpaid past due date, no dispute raised. |
| `invoice_disputed` | b2b | — | Payer has formally contested the invoice. **STOP cause.** |
| `awaiting_po` | b2b | — | Payer's process is blocked pending a purchase order. |
| `unclassified` | all three | — | Classifier could not resolve a cause. **Fallback only.** |

**`STOP_IF_CAUSE_IN = ["user_revoked", "invoice_disputed"]`** — exactly these two,
matching `04_SRS_RevFlow.md` §3.1.1.

The NPCI family column is descriptive framing for the pitch. It is not a lookup
key and nothing in the code branches on it.

### 2.3 `action` — 5 values

Per `04_SRS_RevFlow.md` FR-5, no other action value is valid anywhere in the
system.

| Value | Real or simulated | Meaning |
|---|---|---|
| `retry_now` | **Real** | Execute a Razorpay Test Mode payment attempt immediately. |
| `retry_later` | Neither | Defer this event; re-evaluate on a subsequent pass. No outbound effect. |
| `nudge` | **Simulated** | Generate outreach copy (SMS/WhatsApp/voice script). Written to DB, never transmitted. |
| `escalate_to_human` | Neither | Place in the human-review queue. No outbound effect. |
| `stop` | Neither | Take no action and take no further action on this event. |

`retry_later` covers both "wait for cooldown before retrying a payment" and
"this B2B invoice is not yet old enough for a ladder step." Both are "defer and
re-evaluate," which is why one value serves both.

### 2.4 `ladder_step` — 4 values

**This is a separate field from `action`.** `flag_for_human` is a ladder step,
not an action. This distinction is mandatory: putting `gentle_reminder` or
`flag_for_human` into the `action` column violates FR-5 and breaks the
Exceptions screen filter.

| Value | Paired action | Meaning |
|---|---|---|
| `none` | any | Not a B2B ladder event, or ladder not yet engaged. |
| `gentle_reminder` | `nudge` | First contact. Polite, assumes oversight. |
| `firm_reminder` | `nudge` | Second contact. Direct, references the earlier reminder. |
| `flag_for_human` | `escalate_to_human` | Ladder exhausted. Human review queue. Never auto-escalates to legal or collections (FR-17). |

### 2.5 `outcome` — 8 values

| Value | Set by | Valid for actions |
|---|---|---|
| `recovered` | Executor, after a real Test Mode attempt succeeded | `retry_now` |
| `failed` | Executor, after a real Test Mode attempt was declined | `retry_now` |
| `api_error` | Executor, after an external call errored or could not be made | `retry_now` |
| `simulated` | Simulated Comms Writer | `nudge` |
| `pending` | Policy Engine | `retry_later` |
| `paused` | PTP Tracker | `retry_later` |
| `escalated` | Escalation Queue writer | `escalate_to_human` |
| `withheld` | Policy Engine hard stop | `stop` |

Any other action/outcome pairing is a bug. Validate the pairing before insert.

### 2.6 `rule_fired` — 11 values

The rule that authorised or blocked the decision. Required, non-null, on every
audit row (FR-15, FR-26). This column is what makes `TEST-1` assertable.

| Value | Stage | Meaning |
|---|---|---|
| `hard_stop_cause_in_denylist` | 1 | Cause is in `STOP_IF_CAUSE_IN`. No LLM call made. |
| `retry_ceiling_reached` | 2 | `retry_count >= MAX_RETRIES`. |
| `ptp_pause_active` | 2 | An active promise-to-pay covers this event. |
| `ptp_promise_broken_escalated` | 2 | Promised date passed with no payment; resumed one step up. |
| `contact_cap_reached` | 2 | Customer already contacted today at the daily cap. |
| `cooldown_active` | 2 | Last attempt was inside `COOLDOWN_HOURS`. |
| `ladder_not_yet_due` | 3 | B2B invoice younger than the first ladder threshold. |
| `ladder_step_by_age` | 3 | B2B ladder step assigned deterministically from invoice age. |
| `deterministic_action_table` | 3 | Action resolved from the Section 4.3 decision table. No LLM call made. |
| `llm_reasoned_within_ceiling` | 4 | LLM selected a valid action from the closed allow-list. |
| `llm_output_rejected_defaulted` | 4 | LLM output was invalid or unavailable; defaulted to `escalate_to_human`. |

### 2.7 `cause_source` — 2 values

`rule` or `llm`. Required on every audit row (FR-3).

### 2.8 `simulated_channel` — 3 values

`sms`, `whatsapp`, `voice_script`.

### 2.9 `locale` — 3 values

`en`, `hi`, `hinglish`.

### 2.10 `ptp_status` — 3 values

`active`, `kept`, `broken`.

### 2.11 `batch_run_status` — 3 values

`running`, `completed`, `failed`.

---

## 3. Database schema (complete and closed)

SQLite. Seven tables. This is the entire schema — there are no other tables and
no other columns. `05_System_Architecture_RevFlow.md` §4 describes these
conceptually; this section is the authority on fields and types.

All monetary columns are named with an `_inr` suffix and stored as `INTEGER`
**paise** (1 rupee = 100 paise) to avoid floating-point drift. Convert to rupees
only at the presentation layer.

### 3.1 `batch_runs`

Every run of `run_batch.py` creates exactly one row. This table is what makes
"two clean runs with identical structural behaviour" (`07` BUG-2) verifiable by
diffing two `run_id` values.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `run_id` | TEXT | PK | `RUN-` + UTC `YYYYMMDDTHHMMSS`, e.g. `RUN-20260823T104500` |
| `started_at` | TEXT | NOT NULL | ISO 8601 UTC |
| `completed_at` | TEXT | NULL | ISO 8601 UTC; null while running |
| `status` | TEXT | NOT NULL | `batch_run_status` enum (§2.11) |
| `event_count` | INTEGER | NOT NULL DEFAULT 0 | Events ingested this run |
| `llm_call_count` | INTEGER | NOT NULL DEFAULT 0 | Total LLM calls this run, for the §5.4 metric |
| `random_seed` | INTEGER | NOT NULL | Seed used by the generator; enables reproducibility |
| `notes` | TEXT | NULL | Free text, e.g. `--no-llm` mode flag |

### 3.2 `events`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `event_id` | TEXT | PK | `EVT-` + 4-digit zero-padded, per run: `EVT-0001`…`EVT-0300` |
| `run_id` | TEXT | NOT NULL, FK → `batch_runs.run_id` | |
| `event_type` | TEXT | NOT NULL | `event_type` enum (§2.1) |
| `amount_inr` | INTEGER | NOT NULL | Paise. Amount at risk for this event. |
| `currency` | TEXT | NOT NULL DEFAULT `'INR'` | Always `INR` in Phase 0 |
| `customer_id` | TEXT | NOT NULL | `CUST-` + 4 digits |
| `decline_code` | TEXT | NULL | Source metadata. Null for `b2b_receivable` and `user_abandoned`. |
| `decline_message` | TEXT | NULL | Free-text; the field that forces the LLM classifier path when `decline_code` is unmappable |
| `true_cause` | TEXT | NULL | Ground truth. **Synthetic data only.** Never read by the classifier, policy engine, or executor — read only by the §5.4 evaluation step. |
| `retry_count` | INTEGER | NOT NULL DEFAULT 0 | Attempts already made before this event was ingested |
| `last_attempt_at` | TEXT | NULL | ISO 8601 UTC; drives the `cooldown_active` check |
| `paused_until` | TEXT | NULL | ISO 8601 date; set by the PTP Tracker (FR-20) |
| `ladder_step` | TEXT | NOT NULL DEFAULT `'none'` | `ladder_step` enum (§2.4); current step for this invoice |
| `invoice_issued_at` | TEXT | NULL | ISO 8601 date. `b2b_receivable` only. |
| `invoice_due_date` | TEXT | NULL | ISO 8601 date. `b2b_receivable` only. Ladder age is measured from this. |
| `session_started_at` | TEXT | NULL | ISO 8601 UTC. `checkout_dropoff` only; drives the FR-8 session window. |
| `checkout_resume_token` | TEXT | NULL | Opaque token for the FR-10 resumable link. Generated, never sent. |
| `customer_reply_text` | TEXT | NULL | Simulated inbound reply. Input to PTP detection (FR-19). |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC |

`invoice_age_days` is **derived, never stored**: `(run date − invoice_due_date)`
in whole days. Compute it in one function, `invoice_age_days(event, as_of)`.

### 3.3 `audit_log`

Append-only. One row per policy decision. Written **before** the executor acts
(FR-27). No `UPDATE` or `DELETE` statement may target this table.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `run_id` | TEXT | NOT NULL, FK → `batch_runs.run_id` | |
| `event_id` | TEXT | NOT NULL, FK → `events.event_id` | |
| `event_type` | TEXT | NOT NULL | Denormalised from `events` so metrics need no join |
| `cause` | TEXT | NOT NULL | `cause` enum (§2.2) |
| `cause_source` | TEXT | NOT NULL | `cause_source` enum (§2.7) |
| `rule_fired` | TEXT | NOT NULL | `rule_fired` enum (§2.6) |
| `action` | TEXT | NOT NULL | `action` enum (§2.3) |
| `ladder_step` | TEXT | NOT NULL DEFAULT `'none'` | `ladder_step` enum (§2.4) |
| `rationale` | TEXT | NOT NULL, length ≥ 10 | Human-readable. Enforce non-empty in code (FR-7). |
| `outcome` | TEXT | NOT NULL | `outcome` enum (§2.5). Must be valid for `action` per §2.5. |
| `amount_inr` | INTEGER | NOT NULL | Paise; copied from the event at decision time |
| `attributed_recovery_inr` | INTEGER | NOT NULL DEFAULT 0 | Paise. Non-zero **only** when `outcome = 'recovered'`. See §5.2. |
| `is_simulated` | INTEGER | NOT NULL DEFAULT 0 | 1 when `action = 'nudge'`, else 0 (FR-28) |
| `llm_calls_used` | INTEGER | NOT NULL DEFAULT 0 | 0, 1, or 2 for this decision |
| `latency_ms` | INTEGER | NOT NULL | Decision-to-audit-write latency, for NFR-6 |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC |

### 3.4 `simulated_actions`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `audit_log_id` | INTEGER | NOT NULL, FK → `audit_log.id` | |
| `channel` | TEXT | NOT NULL | `simulated_channel` enum (§2.8) |
| `locale` | TEXT | NOT NULL | `locale` enum (§2.9) |
| `body_text` | TEXT | NOT NULL | The generated copy or voice script |
| `tts_audio_path` | TEXT | NULL | Relative path to the one sample clip (FR-23) |
| `status` | TEXT | NOT NULL DEFAULT `'simulated'` | Only ever `'simulated'`. Present so the value is explicit in the data, not implied. |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC |

### 3.5 `escalations`

Write-only from the executor, read-only from the UI (`05` §3.4).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `audit_log_id` | INTEGER | NOT NULL, FK → `audit_log.id` | |
| `reason` | TEXT | NOT NULL | Short code, mirrors the `rule_fired` that caused escalation |
| `ladder_step` | TEXT | NOT NULL DEFAULT `'none'` | `flag_for_human` for B2B ladder exhaustion |
| `queue` | TEXT | NOT NULL | `ops_review` or `finance_review` |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC |

There is deliberately no `reviewed` column. "Mark Reviewed" on the Exceptions
screen is frontend-local state only (`06` §4.3) so the dashboard remains a pure
read layer (`05` §3.6).

### 3.6 `contact_log`

Authoritative source for the FR-11 contact-frequency cap. Written whenever a
`nudge` is issued.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `run_id` | TEXT | NOT NULL, FK → `batch_runs.run_id` | |
| `customer_id` | TEXT | NOT NULL | |
| `contact_date` | TEXT | NOT NULL | ISO 8601 **date** only, not datetime |
| `audit_log_id` | INTEGER | NOT NULL, FK → `audit_log.id` | |

Unique index on `(run_id, customer_id, contact_date, audit_log_id)`. The cap
check is `SELECT COUNT(*) ... WHERE run_id = ? AND customer_id = ? AND
contact_date = ?` compared against `MAX_CONTACTS_PER_CUSTOMER_PER_DAY`.

### 3.7 `ptp_commitments`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `run_id` | TEXT | NOT NULL, FK → `batch_runs.run_id` | |
| `event_id` | TEXT | NOT NULL, FK → `events.event_id` | |
| `promised_date` | TEXT | NOT NULL | ISO 8601 date, extracted by FR-19 |
| `detected_from_text` | TEXT | NOT NULL | The reply substring the date was extracted from — makes detection auditable |
| `detection_source` | TEXT | NOT NULL | `cause_source` enum: `rule` (regex) or `llm` |
| `status` | TEXT | NOT NULL | `ptp_status` enum (§2.10) |
| `ladder_step_at_pause` | TEXT | NOT NULL | The step to resume *above* if broken (FR-21) |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC |

### 3.8 Entity relationships

```text
batch_runs (1) ──< events (many)
batch_runs (1) ──< audit_log (many)
events     (1) ──< audit_log (many)          one event can accrue several decisions
audit_log  (1) ──< simulated_actions (0..1)  only when action = 'nudge'
audit_log  (1) ──< escalations (0..1)        only when action = 'escalate_to_human'
audit_log  (1) ──< contact_log (0..1)        only when action = 'nudge'
events     (1) ──< ptp_commitments (0..n)
```

### 3.9 Data lifecycle — append-only, run-scoped

**Nothing is ever truncated.** Each `run_batch.py` execution mints a new
`run_id` and inserts a fresh set of `events` under it. Two runs coexist in the
same database.

This replaces any "truncate and repopulate" description: truncating `events`
while appending to `audit_log` would orphan foreign keys and break the audit
trail, which is the one thing the system cannot afford to break.

- The dashboard defaults to the **most recent completed run**.
- `GET /runs` lists all runs so a specific one can be selected.
- A "clean database state" for testing (NFR-8) means a fresh database file, which
  `make reset` provides by deleting `revflow.db`.

---

## 4. Policy configuration and the decision pipeline

### 4.1 Configuration constants (single source of truth)

Defined once in `backend/revflow/contracts/config.py` as module-level
constants. Exposed read-only via `GET /config` (§7.7). Not editable at runtime
in Phase 0 — the ceiling is global by design (`05` §10).

| Constant | Value | Unit | Governs |
|---|---|---|---|
| `MAX_RETRIES` | `3` | attempts | FR-14 retry ceiling |
| `COOLDOWN_HOURS` | `24` | hours | FR-14 minimum gap between attempts |
| `RETRY_BACKOFF_HOURS` | `[24, 48, 96]` | hours | FR-14 exponential backoff schedule, indexed by `retry_count` |
| `CHECKOUT_SESSION_WINDOW_MINUTES` | `15` | minutes | FR-8 abandonment detection window |
| `MAX_CONTACTS_PER_CUSTOMER_PER_DAY` | `1` | contacts | FR-11 frequency cap |
| `STOP_IF_CAUSE_IN` | `["user_revoked", "invoice_disputed"]` | — | FR-6 hard stop |
| `LADDER_GENTLE_AFTER_DAYS` | `7` | days past due | FR-16 |
| `LADDER_FIRM_AFTER_DAYS` | `21` | days past due | FR-16 |
| `LADDER_FLAG_AFTER_DAYS` | `45` | days past due | FR-16 |
| `PTP_GRACE_DAYS` | `2` | days | Grace after `promised_date` before marking `broken` |
| `LLM_CALL_BUDGET_PER_RUN` | `90` | calls | Hard abort ceiling; protects the free tier |
| `LLM_MAX_ATTEMPTS` | `3` | attempts | Retry/backoff on a failed LLM call |
| `LLM_TIMEOUT_SECONDS` | `20` | seconds | Per-call timeout |
| `BATCH_SIZE` | `300` | events | Synthetic batch size (NFR-8) |
| `RANDOM_SEED` | `42` | — | Generator seed; makes BUG-2 reproducibility achievable |
| `DECISION_LATENCY_BUDGET_MS` | `5000` | ms | NFR-6 |

`RANDOM_SEED` is load-bearing. `07_Development_Plan_RevFlow.md` BUG-2 requires
two clean runs with identical structural behaviour; that is only assertable if
the generator is deterministic.

### 4.2 Policy Engine — four ordered stages

The order is the architecture. Stages 1–3 are pure Python with no network I/O.
Stage 4 is the only stage that may call an LLM, and it is reached by a minority
of events.

```text
Stage 1  Hard stop check                 deterministic, no I/O, short-circuits
Stage 2  Guard checks                    deterministic, DB reads only, short-circuits
           2a  retry ceiling
           2b  PTP pause / broken promise
           2c  cooldown
           2d  contact-frequency cap
Stage 3  Deterministic action table      deterministic, table lookup (§4.3)
Stage 4  Bounded LLM action selection    only if Stage 3 has no matching row
```

**Stage 3 is not optional.** `01_PRD_RevFlow.md` §9 reports "% of events resolved
by deterministic rules vs. LLM fallback" as a success metric, and
`03_Roadmap_RevFlow.md` §3 states that the ceiling means most events never reach
the LLM at all. Both are only true if action selection has a deterministic path.
Stage 3 provides it. Expected outcome on the specified dataset: roughly 88% of
events are decided without any LLM call.

Stage 4 is reached only when `cause = 'unclassified'`, or when a
`(event_type, cause)` pair has no row in the §4.3 table. The prompt presents the
remaining allowed actions as a closed list; the response is validated against
that list **in code** before it is trusted. Invalid, unparseable, timed-out, or
budget-exceeded → `action = escalate_to_human`,
`rule_fired = llm_output_rejected_defaulted`. The system fails toward caution.

### 4.3 Deterministic action table (Stage 3)

Evaluate rows top to bottom; first match wins. `age` means `invoice_age_days`.

| # | `event_type` | `cause` | Condition | → `action` | → `ladder_step` | `rule_fired` |
|---|---|---|---|---|---|---|
| 1 | any | `user_revoked` | — | `stop` | `none` | `hard_stop_cause_in_denylist` |
| 2 | any | `invoice_disputed` | — | `stop` | `none` | `hard_stop_cause_in_denylist` |
| 3 | any | any | `retry_count >= MAX_RETRIES` | `escalate_to_human` | unchanged | `retry_ceiling_reached` |
| 4 | `checkout_dropoff` | `technical_decline` | — | `retry_now` | `none` | `deterministic_action_table` |
| 5 | `checkout_dropoff` | `bank_timeout` | — | `retry_now` | `none` | `deterministic_action_table` |
| 6 | `checkout_dropoff` | `insufficient_funds` | `retry_count == 0` | `retry_later` | `none` | `deterministic_action_table` |
| 7 | `checkout_dropoff` | `insufficient_funds` | `retry_count >= 1` | `nudge` | `none` | `deterministic_action_table` |
| 8 | `checkout_dropoff` | `business_decline` | — | `nudge` | `none` | `deterministic_action_table` |
| 9 | `checkout_dropoff` | `authentication_failed` | — | `nudge` | `none` | `deterministic_action_table` |
| 10 | `checkout_dropoff` | `session_timeout` | — | `nudge` | `none` | `deterministic_action_table` |
| 11 | `checkout_dropoff` | `user_abandoned` | — | `nudge` | `none` | `deterministic_action_table` |
| 12 | `subscription_failure` | `bank_timeout` | — | `retry_now` | `none` | `deterministic_action_table` |
| 13 | `subscription_failure` | `technical_decline` | — | `retry_now` | `none` | `deterministic_action_table` |
| 14 | `subscription_failure` | `insufficient_funds` | — | `retry_later` | `none` | `deterministic_action_table` |
| 15 | `subscription_failure` | `mandate_expired` | — | `nudge` | `none` | `deterministic_action_table` |
| 16 | `b2b_receivable` | `awaiting_po` | — | `escalate_to_human` | `flag_for_human` | `deterministic_action_table` |
| 17 | `b2b_receivable` | `invoice_overdue` | `age >= 45` | `escalate_to_human` | `flag_for_human` | `ladder_step_by_age` |
| 18 | `b2b_receivable` | `invoice_overdue` | `21 <= age < 45` | `nudge` | `firm_reminder` | `ladder_step_by_age` |
| 19 | `b2b_receivable` | `invoice_overdue` | `7 <= age < 21` | `nudge` | `gentle_reminder` | `ladder_step_by_age` |
| 20 | `b2b_receivable` | `invoice_overdue` | `age < 7` | `retry_later` | `none` | `ladder_not_yet_due` |
| 21 | any | `unclassified` | — | *→ Stage 4* | unchanged | — |

Rows 1–2 satisfy FR-13 and US-4: `mandate_expired` (row 15) never produces a
retry, and `user_revoked` (row 1) never produces anything but `stop`.

**Ladder monotonicity (US-6, FR-16):** an invoice may not skip a step. If
`events.ladder_step` is already `gentle_reminder` and age crosses 45, the next
step is `firm_reminder`, not `flag_for_human` — advance by exactly one step per
decision. The age thresholds determine the *maximum* step reachable, not the step
assigned. The only exception is a hard stop (rows 1–2), which may interrupt at
any point.

### 4.4 PTP pause and resume (Stage 2b)

1. **Detect.** If `events.customer_reply_text` is non-null, run PTP detection:
   a regex pass for explicit date patterns first, LLM fallback only if the regex
   finds commitment language but no parseable date. Record the source in
   `ptp_commitments.detection_source`.
2. **Pause.** On detection, insert a `ptp_commitments` row with
   `status = 'active'`, set `events.paused_until = promised_date`, decide
   `action = retry_later`, `outcome = paused`,
   `rule_fired = ptp_pause_active`. Store the event's current `ladder_step` in
   `ladder_step_at_pause`.
3. **Hold.** While `run_date <= promised_date + PTP_GRACE_DAYS`, any subsequent
   pass returns `retry_later` / `paused` / `ptp_pause_active` immediately at
   Stage 2b.
4. **Resume escalated.** Once `run_date > promised_date + PTP_GRACE_DAYS` with no
   payment, set `status = 'broken'`, advance one step above
   `ladder_step_at_pause`, and record
   `rule_fired = ptp_promise_broken_escalated`. It **never** restarts at
   `gentle_reminder` (FR-21, US-7).

---

## 5. Metrics — definitions and formulas

Every number the dashboard shows is defined here. If a number is not defined
here, it does not get displayed. This section exists because `04_SRS_RevFlow.md`
NFR-7 forbids hardcoded or cherry-picked metrics, and that is only enforceable
against explicit formulas.

### 5.1 The recoverability problem, stated honestly

In Phase 0, only `retry_now` reaches a real payment rail. `nudge` is simulated
and transmits nothing; `retry_later`, `escalate_to_human` and `stop` are
deliberately inert.

Two consequences follow, and both must be surfaced rather than smoothed over:

1. **No rupee can be recovered except by a successful Razorpay Test Mode retry.**
   A blended recovery rate over all 300 events would be dominated by amounts the
   system never had a mechanism to recover.
2. **The `b2b_receivable` pipeline has no `retry_now` path at all** (§4.3 has no
   such row — invoices are chased by reminders, not retried). Its realised
   recovery is therefore structurally `0`, and its realised rate is `null`. This
   is correct behaviour, not a bug, and the UI must present it as a scope
   statement rather than a failure.

So the contract is: report a **scoped** rate, always adjacent to the scope it was
computed over. Never a blended headline.

### 5.2 Amount definitions

Stored in paise, presented in rupees.

| Metric | Formula |
|---|---|
| `at_risk_inr` | `SUM(events.amount_inr)` for the run |
| `addressable_inr` | `SUM(audit_log.amount_inr)` where `action = 'retry_now'` — the only subset with a live recovery mechanism in Phase 0 |
| `realised_recovered_inr` | `SUM(audit_log.attributed_recovery_inr)` where `outcome = 'recovered'` |
| `simulated_outreach_inr` | `SUM(audit_log.amount_inr)` where `action = 'nudge'` — labelled "under simulated outreach", never counted as recovered |
| `deferred_inr` | `SUM(audit_log.amount_inr)` where `action = 'retry_later'` |
| `withheld_inr` | `SUM(audit_log.amount_inr)` where `action = 'stop'` |
| `escalated_inr` | `SUM(audit_log.amount_inr)` where `action = 'escalate_to_human'` |

The five action-scoped amounts (`addressable`, `simulated_outreach`, `deferred`,
`withheld`, `escalated`) partition the run: they MUST sum to `at_risk_inr`.
Assert this in `run_batch.py`. If it fails, an event was decided twice or not at
all.

`attributed_recovery_inr` is set to the event amount **only** when a real Test
Mode attempt returned success. In every other case it is `0`. There is no
projected, modelled, or estimated recovery anywhere in this system.

### 5.3 Rate definitions

| Metric | Formula | Presented as |
|---|---|---|
| `recovery_rate_realised` | `realised_recovered_inr / addressable_inr` | Headline rate. Always rendered beside `addressable_coverage`. |
| `addressable_coverage` | `addressable_inr / at_risk_inr` | "computed on X% of at-risk value that Phase 0 can act on" |
| `retry_success_rate` | `count(outcome='recovered') / count(action='retry_now')` | Attempt-level success; count-weighted, not amount-weighted |
| `recovery_rate_by_pipeline[type]` | `recovery_rate_realised` filtered to one `event_type` | Three bars on the Overview |

`recovery_rate_realised` is amount-weighted; `retry_success_rate` is
count-weighted. They will differ. Label them distinctly — a viewer who conflates
them draws a wrong conclusion.

**Zero denominators.** Where a denominator is `0`, emit JSON `null`, never `0`.
The frontend renders `null` as an em-dash with a tooltip, never as `0%`. This
case is guaranteed to occur for `b2b_receivable` per §5.1, so it is a required
code path, not an edge case.

### 5.4 Boundedness and honesty metrics

These carry the actual argument.

| Metric | Formula | Target |
|---|---|---|
| `withheld_count` | `count(action='stop')` | > 0, non-negotiable |
| `escalated_count` | `count(action='escalate_to_human')` | > 0, non-negotiable |
| `deterministic_share` | `count(llm_calls_used=0) / count(*)` | ≥ 0.80 |
| `llm_call_count` | `batch_runs.llm_call_count` | ≤ `LLM_CALL_BUDGET_PER_RUN` |
| `out_of_bounds_action_count` | `count(action NOT IN ALLOWED_ACTIONS)` | **exactly 0** — NFR-2 |
| `missing_rationale_count` | `count(rationale IS NULL OR length(rationale) < 10)` | **exactly 0** — FR-7 |
| `p95_decision_latency_ms` | 95th percentile of `audit_log.latency_ms` | ≤ `DECISION_LATENCY_BUDGET_MS` |

`out_of_bounds_action_count` and `missing_rationale_count` must be computed and
displayed even though they should always be zero. A guardrail checked only in a
unit test is a claim; one displayed on the dashboard is evidence.

### 5.5 False-positive and harassment cost

`01_PRD_RevFlow.md` §9 and `04_SRS_RevFlow.md` FR-29 require this reported
alongside recovery gains. It needs a formula to be reportable.

**Definition.** A false positive is an event where the system took an outbound or
chargeable action (`retry_now` or `nudge`) on an event whose `true_cause` is in
`STOP_IF_CAUSE_IN` — the system acted where it should have withheld.

| Metric | Formula |
|---|---|
| `false_positive_count` | `count(*)` where `action IN ('retry_now','nudge')` AND `events.true_cause IN STOP_IF_CAUSE_IN` |
| `false_positive_cost_inr` | `SUM(audit_log.amount_inr)` over that same set |
| `harassment_incident_count` | count of `(customer_id, contact_date)` pairs in `contact_log` whose row count exceeds `MAX_CONTACTS_PER_CUSTOMER_PER_DAY` |
| `over_retry_count` | `count(*)` where `action='retry_now'` AND `events.retry_count >= MAX_RETRIES` |

All four should be `0`. Report them whether they are zero or not — NFR-7 forbids
hiding a non-zero value, and a visible zero with a stated formula is more
persuasive than a silent absence.

Note the dependency: this is the **only** metric family that reads `true_cause`.
It is an evaluation-time read, never a decision-time read. If `true_cause` were
visible to the classifier or policy engine, every number here would be
meaningless.

### 5.6 `summary_metrics.json` — exact shape

Written by `run_batch.py` to `backend/data/summary_metrics.json`, served verbatim
by `GET /metrics`. The frontend consumes these key names exactly.

Values below are **type placeholders, not example data.** They are written this
way deliberately: a plausible-looking number here is the single most likely thing
to end up hardcoded as a fallback or committed as a fixture, which NFR-7 forbids.

```json
{
  "run_id": "<string, RUN-YYYYMMDDTHHMMSS>",
  "generated_at": "<string, ISO 8601 UTC>",
  "random_seed": "<int>",
  "llm_mode": "<string, one of: live | cached | disabled>",
  "event_count": "<int>",
  "amounts_inr": {
    "at_risk": "<float, rupees 2dp>",
    "addressable": "<float>",
    "realised_recovered": "<float>",
    "simulated_outreach": "<float>",
    "deferred": "<float>",
    "withheld": "<float>",
    "escalated": "<float>"
  },
  "rates": {
    "recovery_rate_realised": "<float 0..1 | null>",
    "addressable_coverage": "<float 0..1>",
    "retry_success_rate": "<float 0..1 | null>"
  },
  "by_pipeline": {
    "checkout_dropoff": {
      "event_count": "<int>",
      "at_risk_inr": "<float>",
      "addressable_inr": "<float>",
      "realised_recovered_inr": "<float>",
      "recovery_rate_realised": "<float 0..1 | null>"
    },
    "subscription_failure": { "...": "same five keys" },
    "b2b_receivable":       { "...": "same five keys, but",
                              "recovery_rate_realised": "null by design — see 5.1" }
  },
  "boundedness": {
    "withheld_count": "<int, > 0>",
    "escalated_count": "<int, > 0>",
    "deterministic_share": "<float 0..1>",
    "llm_call_count": "<int>",
    "llm_call_budget": "<int>",
    "out_of_bounds_action_count": "<int, must be 0>",
    "missing_rationale_count": "<int, must be 0>",
    "p95_decision_latency_ms": "<int>"
  },
  "integrity": {
    "false_positive_count": "<int, must be 0>",
    "false_positive_cost_inr": "<float, must be 0.00>",
    "harassment_incident_count": "<int, must be 0>",
    "over_retry_count": "<int, must be 0>"
  },
  "action_breakdown": {
    "retry_now":   "<int>",
    "retry_later": "<int>",
    "nudge":       "<int>",
    "escalate_to_human": "<int>",
    "stop":        "<int>"
  },
  "outcome_breakdown": {
    "recovered": "<int>",
    "failed":    "<int>",
    "api_error": "<int>",
    "simulated": "<int>",
    "pending":   "<int>",
    "paused":    "<int>",
    "escalated": "<int>",
    "withheld":  "<int>"
  }
}
```

**Invariants to assert in `run_batch.py`** (these, not specific values, are what
the build is held to):

1. `sum(action_breakdown.values()) == event_count`
2. `sum(outcome_breakdown.values()) == event_count`
3. `addressable + simulated_outreach + deferred + withheld + escalated == at_risk` (within 1 paise)
4. `recovered + failed + api_error == action_breakdown.retry_now`
5. `simulated == action_breakdown.nudge`
6. `pending + paused == action_breakdown.retry_later`
7. `escalated == action_breakdown.escalate_to_human`
8. `withheld == action_breakdown.stop`
9. every value under `integrity` is `0`
10. `out_of_bounds_action_count == 0` and `missing_rationale_count == 0`

Amounts are rupees with two decimals in JSON, converted from paise on write.
Rates are unrounded floats in `[0, 1]` or `null`; the frontend formats them.

### 5.7 `classifier_metrics.json` — exact shape

Written to `backend/data/classifier_metrics.json`, served by
`GET /classifier-metrics`. Satisfies FR-4. Same placeholder convention.

```json
{
  "run_id": "<string>",
  "generated_at": "<string, ISO 8601 UTC>",
  "overall": {
    "accuracy":        "<float>",
    "macro_precision": "<float>",
    "macro_recall":    "<float>",
    "support":         "<int>"
  },
  "by_cause": {
    "<cause enum value>": {
      "precision": "<float>",
      "recall":    "<float>",
      "f1":        "<float>",
      "support":   "<int>"
    }
  },
  "by_source": {
    "rule": { "count": "<int>", "accuracy": "<float>" },
    "llm":  { "count": "<int>", "accuracy": "<float>" }
  },
  "confusion_pairs": [
    { "true_cause": "<cause>", "predicted_cause": "<cause>", "count": "<int>" }
  ]
}
```

Two reporting rules:

- **Report `by_source` separately.** Rule-path accuracy near `1.0` is expected and
  uninteresting; LLM-path accuracy on the ambiguous subset is the number that
  actually says something. Averaging them hides it.
- **Both STOP causes must reach precision and recall of `1.00`.** Anything less is
  a P0 defect: a missed `user_revoked` is a real-world harassment event, and a
  false `user_revoked` silently abandons recoverable revenue.

`by_cause` must contain an entry for every cause with non-zero support in the run.
Causes with zero support are omitted, not reported as `0.0`.

---

## 6. Synthetic dataset contract

Produced by `backend/scripts/generate_dataset.py`, seeded with `RANDOM_SEED`.
Output: `backend/data/synthetic_events.json`. Satisfies `07` BE-1.

The distribution is grounded in the statistics cited in
`02_Teardown_RevFlow.md` §1 and must be stated openly in the README, per the
assumption declared in `04_SRS_RevFlow.md` §2.6.

### 6.1 Pipeline split — 300 events

| `event_type` | Count | Share | Grounding |
|---|---|---|---|
| `checkout_dropoff` | 150 | 50% | Highest-volume leakage surface |
| `subscription_failure` | 100 | 33% | UPI Autopay 30–50% success rate (Teardown §1) |
| `b2b_receivable` | 50 | 17% | Lower volume, far higher value per event |

### 6.2 Cause distribution

**`checkout_dropoff` — 150.** 105 events (70%) carry a payment-failure cause,
matching the Teardown §1 finding that nearly 70% of Indian cart abandonment is
linked to payment failure rather than indecision or shipping cost.

| `true_cause` | Count |
|---|---|
| `insufficient_funds` | 33 |
| `technical_decline` | 28 |
| `bank_timeout` | 20 |
| `authentication_failed` | 14 |
| `business_decline` | 10 |
| *payment-failure subtotal* | *105* |
| `session_timeout` | 20 |
| `user_abandoned` | 25 |
| **Total** | **150** |

**`subscription_failure` — 100.**

| `true_cause` | Count |
|---|---|
| `insufficient_funds` | 45 |
| `bank_timeout` | 22 |
| `mandate_expired` | 21 |
| `user_revoked` | 12 |
| **Total** | **100** |

**`b2b_receivable` — 50.**

| `true_cause` | Count |
|---|---|
| `invoice_overdue` | 34 |
| `awaiting_po` | 9 |
| `invoice_disputed` | 7 |
| **Total** | **50** |

**Guaranteed minimums.** `user_revoked` ≥ 12 and `invoice_disputed` ≥ 7, giving
**19 hard-stop events**. This is not cosmetic: `01_PRD_RevFlow.md` §13 and US-9
require at least one withheld case reachable from the Exceptions screen, and an
empty Exceptions screen would invalidate the central claim of the product.

### 6.3 The ambiguous subset — forcing a real LLM path

**36 events (12%) are marked ambiguous.** This is an overlay across the
distribution above, not a separate cause: an ambiguous event keeps its
`true_cause`, but its `decline_code` is set to `null` or to a code absent from the
rules map, and `decline_message` is populated with free text
(e.g. `"txn could not be completed, please contact issuing bank"`).

These 36 events are the only ones that reach the LLM classifier. This yields
`by_source.rule.count == 264` and `by_source.llm.count == 36` in
`classifier_metrics.json`.

**Why this matters.** If every `decline_code` mapped cleanly, the rules dict would
score 100% precision by construction and FR-4 would measure nothing. The
ambiguous subset is what makes classifier precision/recall a real measurement
rather than a tautology — and it is also the honest representation of production,
where a meaningful fraction of failures arrive with unhelpful metadata.

None of the 19 hard-stop events may be marked ambiguous. `user_revoked` and
`invoice_disputed` must always be deterministically resolvable, because §5.7
requires them at precision and recall `1.00`.

### 6.4 Amount ranges

Log-uniform within each range, so the distribution is realistically skewed rather
than flat.

| `event_type` | Range (₹) | Rationale |
|---|---|---|
| `checkout_dropoff` | 299 – 9,999 | Consumer cart |
| `subscription_failure` | 99 – 4,999 | Monthly plan value |
| `b2b_receivable` | 15,000 – 2,50,000 | Invoice value |

B2B will dominate `at_risk_inr` by a wide margin while representing 17% of
events. That is realistic and is precisely why FR-29 requires per-pipeline
breakdown — a blended number would be a B2B number wearing a disguise.

### 6.5 `retry_count` distribution

Applies to `checkout_dropoff` and `subscription_failure` only. `b2b_receivable`
events always have `retry_count = 0`.

| `retry_count` | Share | Effect |
|---|---|---|
| 0 | 70% | Normal path |
| 1 | 20% | Backoff applies |
| 2 | 7% | Backoff applies |
| 3 | 3% | **Hits `MAX_RETRIES`** → `escalate_to_human` |

The 3% at the ceiling (~8 events) exist so `TEST-2` has real data to assert
against and so the Exceptions screen shows genuine ceiling escalations, not only
B2B flags.

### 6.6 Invoice ageing — `b2b_receivable`

For the 34 `invoice_overdue` events, `invoice_due_date` is set so
`invoice_age_days` falls in these bands:

| Age band (days past due) | Count | Starting `ladder_step` | Advances to |
|---|---|---|---|
| < 7 | 5 | `none` | stays `none` → `retry_later` |
| 7 – 20 | 12 | `none` | `gentle_reminder` |
| 21 – 44 | 11 | `gentle_reminder` | `firm_reminder` |
| ≥ 45 | 6 | `firm_reminder` | `flag_for_human` |
| **Total** | **34** | | |

**The starting `ladder_step` column is load-bearing.** Ladder monotonicity (§4.3)
forbids skipping steps, so an event arriving at `ladder_step = 'none'` with an age
of 50 days would advance only to `gentle_reminder` on its first pass. Seeding
each event at one step below its age-implied ceiling means a **single** batch run
exercises and displays all three ladder steps — which is exactly what
`03_Roadmap_RevFlow.md` §5 requires ("ladder step assignment visibly changes with
invoice age in the audit log").

The 9 `awaiting_po` and 7 `invoice_disputed` events also carry realistic due
dates, but their action is determined by cause, not age.

### 6.7 Simulated customer replies and PTP seeding

20 events carry non-null `customer_reply_text`:

| Pipeline | Replies | Contain a parseable PTP | Contain commitment language but no clear date | No commitment |
|---|---|---|---|---|
| `b2b_receivable` | 15 | 8 | 3 | 4 |
| `subscription_failure` | 5 | 3 | 1 | 1 |
| **Total** | **20** | **11** | **4** | **5** |

- The **11 parseable** replies are handled by the regex path.
- The **4 with commitment language but no clear date** (e.g. "will settle this
  next week") are the LLM PTP-extraction path. They count against
  `LLM_CALL_BUDGET_PER_RUN`.
- Of the 11 parseable PTPs, **7 have a future `promised_date`** (→ `active`,
  `outcome = paused`) and **4 have a past `promised_date` beyond
  `PTP_GRACE_DAYS`** (→ `broken`, resume one step escalated).

Both PTP outcomes must be present in a single run. A run showing only pauses
proves FR-20 but leaves FR-21 and US-7 unevidenced, and the broken-promise
escalation is the more interesting behaviour of the two.

No reply text may be attached to a `user_revoked` or `invoice_disputed` event —
a hard stop must never be reachable by a PTP pause, or the two guardrails would
interact in a way neither document specifies.

### 6.8 Identifiers and reproducibility

- `event_id`: `EVT-0001` … `EVT-0300`, assigned in generation order.
- `customer_id`: `CUST-0001` … `CUST-0240`. Fewer customers than events, so some
  customers own several events — required to exercise the FR-11 contact cap.
- **At least 6 customers must own 2+ `nudge`-bound events on the same date**, so
  `contact_cap_reached` actually fires and `harassment_incident_count` is a
  tested `0` rather than an untested one.
- Running the generator twice with the same `RANDOM_SEED` MUST produce a
  byte-identical file. Assert this in `TEST-9`.

---

## 7. API contract

FastAPI, served on **port 8000**. Frontend runs on **port 3000**. CORS must allow
`http://localhost:3000` — without it every frontend fetch fails with an opaque
network error, which is a costly way to lose an afternoon.

Base path: none (routes are at root). All responses `application/json`.

Ten endpoints. This list is complete.

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | GET | `/health` | Liveness |
| 2 | POST | `/run-batch` | Trigger a batch run |
| 3 | GET | `/runs` | List runs |
| 4 | GET | `/metrics` | Overview screen data |
| 5 | GET | `/classifier-metrics` | Classifier precision/recall |
| 6 | GET | `/audit-log` | Audit Trail screen data |
| 7 | GET | `/exceptions` | Exceptions screen data |
| 8 | GET | `/events/{event_id}` | Event Detail Drawer data |
| 9 | GET | `/config` | Read-only policy ceiling values |
| 10 | POST | `/webhook` | Single-event ingestion |

### 7.1 `GET /health`

`200` → `{"status": "ok", "version": "<string>", "db": "connected", "razorpay_mode": "test"}`

`razorpay_mode` MUST read `"test"`. If the key does not match `^rzp_test_`, the
application refuses to start (§8.3), so this field can never legitimately report
anything else.

### 7.2 `POST /run-batch`

**This endpoint was absent from the v1 architecture while "Run Batch" was the
primary button on every screen** (`06` §3, §4.5, §5.3). It is required.

Request body: `{"use_llm": <bool, default true>, "regenerate_dataset": <bool, default true>}`

`202 Accepted` → `{"run_id": "<string>", "status": "running", "poll": "/runs"}`

Runs the pipeline in a FastAPI background task. Returns immediately — a 300-event
run exceeds any reasonable HTTP timeout. The frontend polls `GET /runs` until the
run's `status` is `completed` or `failed`, then refetches `/metrics`.

`409 Conflict` if a run is already in progress. The frontend also disables the
button while running (`06` §7.1), but the server must enforce it too: a
double-click must not be able to corrupt a run.

`use_llm: false` runs Stage 4 in disabled mode — every event that would have
reached the LLM is decided `escalate_to_human` with
`rule_fired = llm_output_rejected_defaulted` and
`summary_metrics.json.llm_mode = "disabled"`. This is the offline fallback that
every risk register in this document set relies on for demo safety.

### 7.3 `GET /runs`

`200` → array of `batch_runs` rows, newest first, each with all §3.1 columns.

### 7.4 `GET /metrics`

Optional `?run_id=` — defaults to the most recent **completed** run.

`200` → the `summary_metrics.json` object exactly as specified in §5.6.

`404` with `{"detail": "no completed runs"}` when the database has no completed
run. The frontend renders the §4.5 empty state on `404` — it must not treat this
as an error toast.

### 7.5 `GET /classifier-metrics`

Optional `?run_id=`. `200` → the §5.7 object. `404` when absent.

### 7.6 `GET /audit-log`

Query parameters, all optional and combinable:

| Param | Type | Notes |
|---|---|---|
| `run_id` | string | Defaults to latest completed run |
| `event_type` | enum §2.1 | |
| `cause` | enum §2.2 | |
| `action` | enum §2.3 | |
| `sort` | `amount` \| `cause` \| `timestamp` | Default `timestamp` |
| `order` | `asc` \| `desc` | Default `desc` |
| `limit` | int, 1–500 | Default 100 |
| `offset` | int | Default 0 |

`200` → `{"run_id": "<string>", "total": <int>, "limit": <int>, "offset": <int>, "rows": [ ... ]}`

Each row carries every §3.3 `audit_log` column plus, flattened for display:
`customer_id`, `decline_code`, `simulated_channel` (null unless a
`simulated_actions` row exists), and `amount_inr` **in rupees** as a float.

An invalid enum value returns `422`, not a silently empty result set. Silent
empties look identical to "no matching data" and will cost debugging time.

### 7.7 `GET /exceptions`

`200` → two pre-grouped arrays, matching the two sections the Exceptions screen
renders (`06` §4.3):

```json
{
  "run_id": "<string>",
  "withheld_by_policy": [ "<audit row, action = stop>" ],
  "needs_a_human":      [ "<audit row, action = escalate_to_human>" ]
}
```

Grouping happens server-side. The frontend must not filter a full audit log
client-side to build this screen — FR-31 requires zero omissions relative to the
audit log, and that guarantee belongs in one place, not in a UI filter.

### 7.8 `GET /events/{event_id}`

Powers the Event Detail Drawer (`06` §4.4). `200` →

```json
{
  "event": "<full events row, §3.2>",
  "timeline": [ "<all audit_log rows for this event, chronological>" ],
  "simulated_actions": [ "<rows, §3.4>" ],
  "escalations": [ "<rows, §3.5>" ],
  "ptp_commitments": [ "<rows, §3.7>" ]
}
```

`404` on unknown `event_id`. `true_cause` MUST be omitted from this response —
exposing ground truth in a UI that a judge will click through invites the
reasonable suspicion that the classifier had access to it.

### 7.9 `GET /config`

`200` → every §4.1 constant as a flat read-only object, plus
`{"editable": false, "note": "Global ceiling, not per-merchant in Phase 0"}`.

Powers the read-only policy panel in `06` §8. Read-only is deliberate: it lets a
judge inspect the ceiling values without any possibility of a live
misconfiguration.

### 7.10 `POST /webhook`

Accepts one Razorpay-shaped event, normalises it through the same ingestion path
as the batch loader, and processes it through the full pipeline.

`202 Accepted` → `{"event_id": "<string>", "run_id": "<string>", "accepted": true}`

This endpoint is **functional in Phase 0**, satisfying FR-1's "synthetic dataset
and/or Razorpay Test Mode webhooks". It is not the primary path and needs no
public tunnel for the demo, but it must work when posted to locally — it is the
proof that the ingestion layer is genuinely source-agnostic (`05` §3.1), which is
the claim the whole Phase 1 migration story rests on.

Events arriving by webhook attach to a synthetic `run_id` of the form
`RUN-WEBHOOK-<date>` so they never contaminate a batch run's metrics.

### 7.11 Endpoints that deliberately do not exist

| Not built | Why |
|---|---|
| `POST /escalations/{id}/review` | "Mark Reviewed" is frontend-local state (`06` §4.3), keeping the dashboard a pure read layer (`05` §3.6) |
| `PUT`/`PATCH` on `/audit-log` | The ledger is append-only (FR-26). No write path may exist. |
| `POST /config` | Ceiling is not runtime-editable in Phase 0 (`05` §10) |
| Any auth endpoint | Single-operator local scope (`04` §4.1) |
| Any send/dispatch endpoint | No real outbound communication exists anywhere (FR-24) |

If a task seems to need one of these, re-read the requirement — it does not.

---

## 8. External adapter contracts

Both external dependencies sit behind thin adapters so the Policy Engine never
imports a vendor SDK. Swapping either must not require touching
`policy/` (`05` §3.2 design decision, `07` §3.5 exit criteria).

### 8.1 LLM adapter

Interface, in `backend/revflow/adapters/llm.py`:

```python
class LLMAdapter(Protocol):
    def classify_cause(
        self, event: Event, allowed_causes: list[str]
    ) -> tuple[str, float] | None: ...

    def select_action(
        self, event: Event, cause: str, allowed_actions: list[str]
    ) -> tuple[str, str] | None: ...

    def generate_outreach(
        self, event: Event, cause: str, locale: str, tone: str
    ) -> str | None: ...

    def extract_ptp_date(self, reply_text: str) -> str | None: ...
```

Every method returns `None` on any failure. `None` is not an exception — it is the
expected, handled signal that the deterministic fallback must take over.

**Call contract.**

- Both `classify_cause` and `select_action` receive their permitted values as an
  explicit closed list, and both responses are validated against that list **in
  Python** before being trusted. Prompt instructions are not a guarantee (`05`
  §3.3).
- Request JSON mode / structured output where the provider supports it. Parse
  defensively regardless.
- `select_action` returns `(action, rationale)`. A response with a valid action but
  an empty or missing rationale is **invalid** — FR-7 requires a rationale, so a
  bare action is not a usable answer.
- Timeout `LLM_TIMEOUT_SECONDS`, up to `LLM_MAX_ATTEMPTS` with exponential
  backoff. After the last attempt, return `None`.
- Increment `batch_runs.llm_call_count` on every attempt, including failed ones —
  a failed call still consumes free-tier quota.
- When `llm_call_count >= LLM_CALL_BUDGET_PER_RUN`, all methods return `None`
  immediately without making a request. The run continues and completes; it does
  not abort. Record this in `batch_runs.notes`.

**Provider selection** via `LLM_PROVIDER` ∈ `{groq, gemini, anthropic}`. One
concrete implementation per provider, one shared validation wrapper. The wrapper
holds the allow-list checking so provider code cannot bypass it.

**Determinism.** Set `temperature = 0`. Structural reproducibility across two runs
(`07` BUG-2) is impossible to assert with a sampling temperature, and there is no
upside to creative variance in a bounded action selection.

### 8.2 Cause mapping: `decline_code` → `cause`

Lives in `backend/revflow/contracts/decline_map.py` as a plain dict, loaded once.

**Read this carefully — it is the single largest hallucination risk in the
project.**

`05_System_Architecture_RevFlow.md` §3.2 states that roughly 80% of real-world
decline codes are well documented under the NPCI Technical/Business Decline
taxonomy. That framing is correct for the pitch. It does **not** license inventing
specific code strings.

Therefore:

1. The Phase 0 map covers exactly the `decline_code` values that
   `generate_dataset.py` emits, and nothing else. Generator and map are written
   together, from the same constant list, in one file
   (`contracts/decline_map.py`) — so they cannot drift.
2. Any `decline_code` not in the map routes to the LLM classifier. Not to a
   guessed cause.
3. **Do not populate this map with real NPCI or Razorpay error codes from
   memory.** If real codes are wanted, they must be copied from live Razorpay
   documentation at implementation time and marked with the date verified. An
   invented-but-plausible code string is worse than an obviously synthetic one,
   because it will not be questioned.
4. Synthetic codes MUST be prefixed `SYN_` (e.g. `SYN_INSUFFICIENT_FUNDS`,
   `SYN_BANK_TIMEOUT`) so no reader can mistake them for production codes. The
   README states this explicitly.

This is the honest version of the claim: the *architecture* is a table lookup that
scales to the real taxonomy, and the *Phase 0 table* is synthetic and labelled as
such. Both statements survive a judge asking where the codes came from.

### 8.3 Razorpay adapter — `retry_now` execution

Interface, in `backend/revflow/adapters/razorpay_client.py`:

```python
class RazorpayAdapter(Protocol):
    def assert_test_mode(self) -> None: ...
    def attempt_recovery(self, event: Event) -> RetryResult: ...

@dataclass
class RetryResult:
    outcome: str          # 'recovered' | 'failed' | 'api_error'
    provider_ref: str | None
    message: str
    raw_status: str | None
```

**Startup assertion (mandatory).** `assert_test_mode()` runs at application start
and at the top of `run_batch.py`. It raises and halts the process unless
`RAZORPAY_KEY_ID` matches `^rzp_test_`. There is no override flag and no
environment variable that disables this check. A build that cannot physically
touch live money is a stronger claim than a build instructed not to.

**Semantics of `retry_now` per pipeline.** "Retry" is a product concept, not a
single API call, and the mapping differs by pipeline:

| `event_type` | What `retry_now` means | Notes |
|---|---|---|
| `checkout_dropoff` | Create a fresh order / payment attempt for the same amount and customer in Test Mode | A new attempt against the same intent, not a mutation of the old one |
| `subscription_failure` | Trigger a charge attempt against the existing test-mode mandate | Only reached for `bank_timeout` / `technical_decline` — never for `mandate_expired` or `user_revoked` (§4.3 rows 1, 15) |
| `b2b_receivable` | **Not applicable.** No §4.3 row produces `retry_now` for B2B. | Invoices are chased, never retried. `assert` this is unreachable. |

**Endpoint discipline.** Bind these semantics only to endpoints verified in
official Razorpay Test Mode documentation at implementation time. Do **not** guess
a path such as a "retry payment" endpoint — resist the shape of the concept
suggesting the shape of a URL. If the required endpoint cannot be verified:

```python
return RetryResult(
    outcome="api_error",
    provider_ref=None,
    message="Razorpay endpoint for <case> not verified; no call attempted",
    raw_status=None,
)
```

An honest `api_error` on the dashboard is a defensible engineering position. A
`404` from a hallucinated URL, silently recorded as a `failed` recovery, corrupts
every metric downstream and is indistinguishable from a real decline.

**Error handling.** Wrap all calls in try/except with exponential backoff, max 3
attempts (`05` §8). Network, auth, and 5xx failures → `api_error`. A genuine
payment decline is **not** an error — it is `failed`, and the distinction matters:
`failed` is signal about payments, `api_error` is signal about our integration.

**Test-mode success rate.** Test Mode outcomes are controllable. Do not force a
flattering rate. Configure a mix producing roughly 50–60% success across attempts,
document the chosen mechanism in the README, and let the measured number be
whatever it is.

### 8.4 The absent messaging adapter

There is no messaging adapter, and its absence is enforced, not assumed
(FR-24, `05` §3.4).

**Prohibited anywhere in the repository:** `twilio`, `plivo`, `exotel`,
`gupshup`, `msg91`, `karix`, `sendgrid`, `mailgun`, `ses`, `boto3`, `whatsapp`,
`smtplib`, or any other message-transmitting client.

`nudge` writes a `simulated_actions` row and nothing else. No HTTP client is
constructed on that path.

`07_Development_Plan_RevFlow.md` DEP-3 includes a repository-wide grep for these
names as a P0 Definition of Done item, so the guarantee is verified rather than
described.

**TTS exception (FR-23).** One sample audio clip is permitted, generated
**locally** — browser Web Speech API, or an offline TTS library writing a file to
disk. Not a cloud speech API, which would mean a network call on an outreach path
and would breach the boundary the architecture is built to demonstrate.

---

## 9. Repository layout

`07_Development_Plan_RevFlow.md` SET-3 requires a folder structure matching the
component boundaries in `05_System_Architecture_RevFlow.md` §3. That document
describes components conceptually; this is the concrete tree. Follow it exactly —
every path referenced in any document resolves here.

```text
revflow/
├── README.md                        # real-vs-simulated disclosure (DEP-2)
├── Makefile                         # reset | generate | run | test | dev
├── .gitignore                       # .env before any .env exists (SET-2)
├── .env.example                     # committed; .env never is
│
├── backend/
│   ├── requirements.txt
│   ├── revflow/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, CORS, startup assertions
│   │   ├── contracts/               # generated from doc 00 — the single source of truth
│   │   │   ├── enums.py             # §2, every closed enum
│   │   │   ├── config.py            # §4.1, every constant
│   │   │   ├── decline_map.py       # §8.2, SYN_ codes + generator constants
│   │   │   └── schemas.py           # Pydantic request/response models, §7
│   │   ├── db/
│   │   │   ├── connection.py
│   │   │   ├── schema.sql           # §3, all seven tables
│   │   │   └── ledger.py            # insert_audit_row() — the ONLY audit write path
│   │   ├── ingestion/
│   │   │   ├── normaliser.py        # both sources → one Event shape
│   │   │   └── batch_loader.py
│   │   ├── classifier/
│   │   │   ├── rules.py             # decline_map lookup
│   │   │   └── llm_fallback.py
│   │   ├── policy/
│   │   │   ├── engine.py            # the four stages, in order (§4.2)
│   │   │   ├── hard_stops.py        # stage 1
│   │   │   ├── guards.py            # stage 2
│   │   │   └── action_table.py      # stage 3 (§4.3)
│   │   ├── executor/
│   │   │   ├── retry.py             # REAL — only module touching a payment rail
│   │   │   ├── simulated_comms.py   # SIMULATED — no network client, ever
│   │   │   └── escalation.py
│   │   ├── ptp/
│   │   │   └── tracker.py
│   │   ├── ladder/
│   │   │   └── b2b.py
│   │   ├── metrics/
│   │   │   ├── summary.py           # §5.6 + the ten invariant assertions
│   │   │   └── classifier_eval.py   # §5.7
│   │   ├── adapters/
│   │   │   ├── llm.py               # §8.1
│   │   │   └── razorpay_client.py   # §8.3
│   │   └── api/
│   │       └── routes.py            # §7, all ten endpoints
│   ├── scripts/
│   │   ├── generate_dataset.py      # §6
│   │   └── run_batch.py             # orchestration entrypoint
│   ├── data/                        # gitignored except .gitkeep
│   │   ├── synthetic_events.json
│   │   ├── summary_metrics.json
│   │   ├── classifier_metrics.json
│   │   ├── revflow.db
│   │   └── audio/sample_hinglish.wav
│   └── tests/
│       ├── test_hard_stops.py       # TEST-1
│       ├── test_retry_ceiling.py    # TEST-2
│       ├── test_llm_bounds.py       # TEST-3
│       ├── test_razorpay_live.py    # TEST-4
│       ├── test_batch_e2e.py        # TEST-5
│       ├── test_ladder.py           # TEST-10
│       ├── test_ptp.py              # TEST-11
│       ├── test_determinism.py      # TEST-9
│       ├── test_contract_parity.py  # TEST-12 — enums.py == contracts.ts
│       └── test_no_messaging.py     # TEST-13 — prohibited-package grep
│
├── frontend/
│   ├── package.json
│   ├── tailwind.config.ts           # tokens from 06 §2
│   ├── app/
│   │   ├── layout.tsx               # fonts, top nav, Run Batch button
│   │   ├── page.tsx                 # Overview          (06 §4.1)
│   │   ├── audit/page.tsx           # Audit Trail       (06 §4.2)
│   │   └── exceptions/page.tsx      # Exceptions        (06 §4.3)
│   ├── components/
│   │   ├── StatCard.tsx
│   │   ├── PipelineBar.tsx
│   │   ├── LedgerRow.tsx
│   │   ├── ActionTag.tsx            # [REAL] / [SIMULATED]
│   │   ├── WithheldStamp.tsx
│   │   ├── FilterChip.tsx
│   │   ├── EventDrawer.tsx          # 06 §4.4
│   │   ├── Toast.tsx
│   │   └── Skeleton.tsx
│   ├── lib/
│   │   ├── api.ts                   # typed fetch wrappers for all ten endpoints
│   │   ├── contracts.ts             # TS unions mirroring §2 — must match enums.py
│   │   └── format.ts               # en-IN currency, §10.2
│   └── styles/globals.css           # CSS custom properties, 06 §2
│
└── docs/
    ├── 00_CONTRACTS_RevFlow.md      # this file
    ├── 01_PRD_RevFlow.md
    ├── 02_Teardown_RevFlow.md
    ├── 03_Roadmap_RevFlow.md
    ├── 04_SRS_RevFlow.md
    ├── 05_System_Architecture_RevFlow.md
    ├── 06_UIUX_RevFlow.md
    ├── 07_Development_Plan_RevFlow.md
    ├── 08_Audit_Report_RevFlow.md
    └── architecture.md              # build output, DEP-1
```

`contracts/enums.py` and `frontend/lib/contracts.ts` are two representations of
§2 and MUST agree. Add a test asserting the Python enum members equal the values
listed in the TS file, so drift fails a test instead of surfacing as a blank UI
filter.

---

## 10. Environment and formatting

### 10.1 Environment variables

`.env.example` is committed with every key present and every value blank. `.env`
is never committed (SET-2, DEP-3).

| Variable | Example | Required | Notes |
|---|---|---|---|
| `RAZORPAY_KEY_ID` | `rzp_test_xxxxxxxx` | yes | Must match `^rzp_test_` (§8.3) |
| `RAZORPAY_KEY_SECRET` | | yes | |
| `LLM_PROVIDER` | `groq` | yes | `groq` \| `gemini` \| `anthropic` |
| `LLM_API_KEY` | | yes | |
| `LLM_MODEL` | | no | Provider default if unset |
| `DATABASE_PATH` | `backend/data/revflow.db` | no | Defaults as shown |
| `API_PORT` | `8000` | no | |
| `CORS_ORIGINS` | `http://localhost:3000` | no | |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | yes (frontend) | Must be `NEXT_PUBLIC_`-prefixed to reach the browser |

No secret is ever read anywhere but through this layer, and none is logged — not
even truncated. NFR-4.

### 10.2 Number and currency formatting

Backend stores paise as integers and emits rupees as floats. All formatting is
frontend-only, in `lib/format.ts`.

| Context | Format | Example |
|---|---|---|
| Stat card headline | `en-IN`, no decimals, `₹` prefix | `₹2,84,600` |
| Ledger row amount | `en-IN`, 2 decimals, monospace, right-aligned | `₹1,200.00` |
| Percentage | 1 decimal, `%` suffix | `69.4%` |
| Null rate | em-dash with tooltip | `—` |
| Timestamp | `en-IN`, `DD MMM YYYY, HH:mm` IST | `23 Aug 2026, 14:05` |

Use `Intl.NumberFormat('en-IN')` — lakh/crore grouping is not what a naive
thousands separator produces, and `₹410200` where `₹4,10,200` belongs reads as
sloppy to precisely the Indian audience this product targets.

Timestamps are stored UTC and displayed IST (`Asia/Kolkata`). Convert once, at
the formatting boundary.

### 10.3 Fonts

Per `06_UIUX_RevFlow.md` §2.2: Newsreader (display), IBM Plex Sans (body), IBM
Plex Mono (data). Load via `next/font/google` so they are self-hosted at build
time — no runtime CDN request, no layout shift, no external dependency during a
demo on unreliable venue wifi.

---

## 11. Reconciliation tables

The v1 document set assigned three different priorities to the same requirement in
three places, and two different day numbers to the same milestone. These tables
are the settled answer. All other documents defer to them.

### 11.1 Canonical requirement priorities

One priority per requirement, expressed in all three vocabularies at once.

| FR/NFR | Requirement (short) | MoSCoW | Dev plan | PRD tier | Module |
|---|---|---|---|---|---|
| FR-1 | Ingest three event types | Must | P0 | P0 | 1 |
| FR-2 | Classify cause, rules-first, LLM fallback | Must | P0 | P0 | 1 |
| FR-3 | Log `cause_source` | Should | P1 | P1 | 1 |
| FR-4 | Compute classifier precision/recall | **Must** | **P0** | **P0** | 1 |
| FR-5 | Action from the closed set only | Must | P0 | P0 | 2 |
| FR-6 | Deterministic stops before any LLM call | Must | P0 | P0 | 2 |
| FR-7 | Rationale required on every decision | Must | P0 | P0 | 2 |
| FR-8 | Checkout session window | Must | P0 | P0 | 3 |
| FR-9 | Distinguish payment failure from plain exit | Must | P0 | P0 | 3 |
| FR-10 | Resumable checkout link | Should | P1 | P1 | 3 |
| FR-11 | Contact-frequency cap | Must | P0 | P0 | 3 |
| FR-12 | Classify subscription failure causes | Must | P0 | P0 | 3 |
| FR-13 | Never blind-retry expired/revoked mandates | Must | P0 | P0 | 3 |
| FR-14 | Backoff bounded by cooldown and ceiling | Must | P0 | P0 | 3 |
| FR-15 | Attribute every retry to its authorising rule | Must | P0 | P0 | 3 |
| FR-16 | B2B ladder step by invoice age | **Must** | **P0** | **P0** | 5 |
| FR-17 | Never auto-escalate to legal/collections | Must | P0 | P0 | 5 |
| FR-18 | Pause ladder on PTP | **Must** | **P0** | **P0** | 5 |
| FR-19 | Detect PTP and extract date | **Must** | **P0** | **P0** | 4 |
| FR-20 | Pause until promised date | **Must** | **P0** | **P0** | 4 |
| FR-21 | Resume escalated, never restarted | **Must** | **P0** | **P0** | 4 |
| FR-22 | Hinglish script, tone-calibrated by cause | Should | P1 | P1 | 3 |
| FR-23 | One sample TTS clip | Should | P1 | P1 | 3 |
| FR-24 | No real outbound communication | Must | P0 | P0 | 3 |
| FR-25 | Consent-gate future live voice | Deferred | — | P2 | — |
| FR-26 | Append-only audit row per decision | Must | P0 | P0 | 6 |
| FR-27 | No action without an audit row first | Must | P0 | P0 | 6 |
| FR-28 | Label simulated actions in every surface | Must | P0 | P0 | 6 |
| FR-29 | Display the required metric set | Must | P0 | P0 | 6 |
| FR-30 | Sortable, filterable audit trail | Should | P1 | P1 | 6 |
| FR-31 | Exceptions view, zero omissions | Must | P0 | P0 | 6 |
| FR-32 | Run-scoped batches (`batch_runs`) | Must | P0 | P0 | 6 |
| FR-33 | Contact log backing the FR-11 cap | Must | P0 | P0 | 3 |
| FR-34 | Deterministic action table before LLM | Must | P0 | P0 | 2 |
| FR-35 | `POST /run-batch` trigger endpoint | Must | P0 | P0 | 6 |
| FR-36 | Read-only `GET /config` | Should | P1 | P1 | 6 |
| NFR-1 | Auditability | Must | P0 | P0 | — |
| NFR-2 | Boundedness, verified in code | Must | P0 | P0 | — |
| NFR-3 | Explainability | Must | P0 | P0 | — |
| NFR-4 | No card data, no committed secrets | Must | P0 | P0 | — |
| NFR-5 | Consent-gated communication | Must | P0 | P0 | — |
| NFR-6 | Decision latency budget | Should | P1 | P1 | — |
| NFR-7 | Honest, computed metrics | Must | P0 | P0 | — |
| NFR-8 | Unattended clean-state batch run | Must | P0 | P0 | — |
| NFR-9 | Phase 1 migration without redesign | Should | P2 | P2 | — |

**The upgrades in bold.** In the v1 set, PTP tracking (FR-18–21) and the B2B
ladder (FR-16) were simultaneously "Must" in the SRS, "P1 / Nice-to-Have" in the
PRD, "P1" in the development plan, and *mandatory for all six modules* in the
roadmap. They are settled at **P0** because `02_Teardown_RevFlow.md` §4 item 5
names promise-to-pay married to B2B receivables as a whitespace no competitor
occupies. Cutting it would remove a load-bearing differentiator while the
Teardown still claims it. FR-4 is upgraded for the same reason: classifier
precision/recall is a stated success metric in `01_PRD_RevFlow.md` §9, so it
cannot be optional.

### 11.2 Canonical milestones

`03_Roadmap_RevFlow.md` §4 and `07_Development_Plan_RevFlow.md` §5 both reproduce
this table verbatim. It is defined here so they cannot diverge again.

| Milestone | Day | Contents | Exit criteria |
|---|---|---|---|
| **M1** Foundation | 2 | SET-1–4, DB-1–5 | `/health` returns 200; all seven tables round-trip; 300-event dataset generated and byte-reproducible under `RANDOM_SEED` |
| **M2** Core engine | 4 | BE-1–6, INT-1–2 | **TEST-1 passes**: a `user_revoked` event yields `stop` with `llm_calls_used = 0`. TEST-2, TEST-3 pass. |
| **M3** Full pipeline | 5 | BE-7–13 | TEST-5 passes: 300 events end-to-end unattended from a fresh DB; all ten §5.6 invariants hold |
| **M4** Dashboard | 7 | FE-1–7 | All three screens render live data; every displayed number traces to an audit row; ≥1 `stop` clickable on Exceptions |
| **M5** Hardened | 9 | INT-3–4, BE-14, FE-8–9, BUG-1–4, DEP-1–3 | All P0 tests green; two clean runs structurally identical; every module has a clickable real audit example |
| **M6** Submitted | 10 | DEP-5–6 | Repo reproducible from clean checkout; video shows all six modules |

The v1 set placed M1 at Day 1 in the development plan and Day 2 in the roadmap,
and disagreed on whether M2 included the Action Executor. Settled: **M1 exits
Day 2**, and the Action Executor (BE-7 through BE-9) belongs to **M3**, not M2 — M2 is
exactly the classifier plus the policy engine, which keeps its exit criterion
(TEST-1) clean and unambiguous.

### 11.3 Corrected SRS → PRD traceability

The v1 SRS §8 mapped its modules to "PRD Section 4.1–4.7". In the current PRD,
§4 is *Non-Goals* and there is no §4.7. Corrected:

| SRS section | Module | PRD reference |
|---|---|---|
| §3.1 Core Engine | 1, 2 | `01_PRD` §5.1, §5.2 |
| §3.2 Checkout Drop-off | 3 | `01_PRD` §5.3 |
| §3.3 Subscription + Mandate | 3 | `01_PRD` §5.3, US-4, US-5 |
| §3.4 B2B Receivables | 5 | `01_PRD` §5.5, US-6 |
| §3.5 PTP Tracker | 4 | `01_PRD` §5.4, US-7 |
| §3.6 Hinglish Voice | 3 | `01_PRD` §5.3, §4 (non-goal boundary) |
| §3.7 Audit / Dashboard | 6 | `01_PRD` §5.6, §7 (US-1, US-8), §9 |
| §5 NFRs | — | `01_PRD` §3 (goals), §9 (metrics) |
| §7 Compliance | — | `01_PRD` §4 (non-goals), §12 |

### 11.4 The guardrail tests

Four tests are non-negotiable regardless of what else slips
(`07` §3.6, §5). Each maps to a specific contract in this document.

| Test | Asserts | Contract |
|---|---|---|
| **TEST-1** | `user_revoked` and `invoice_disputed` → `stop`, `llm_calls_used = 0`, `rule_fired = hard_stop_cause_in_denylist` | §4.3 rows 1–2, NFR-2 |
| **TEST-2** | `retry_count >= MAX_RETRIES` → `escalate_to_human`, `rule_fired = retry_ceiling_reached` | §4.3 row 3 |
| **TEST-3** | An LLM returning `"delete_customer"`, `""`, malformed JSON, or timing out → `escalate_to_human`, `rule_fired = llm_output_rejected_defaulted` | §8.1 |
| **TEST-5** | 300 events, fresh DB, unattended; all ten §5.6 invariants hold | NFR-8 |

TEST-1 is the single most important test in the project. It is the executable form
of the claim `02_Teardown_RevFlow.md` §4 item 3 makes about Churnkey's over-retry
failure mode. If it does not pass, the product's central differentiator is
unevidenced and nothing else in the build compensates.

---

## 12. Pre-submission verification checklist

Mechanical checks, each one a shell command or a test. Every item is verifiable by
someone with no context.

**Boundedness**

- [ ] TEST-1, TEST-2, TEST-3, TEST-5 pass — run twice, from a wiped database
- [ ] `summary_metrics.json.boundedness.out_of_bounds_action_count == 0`
- [ ] `summary_metrics.json.boundedness.missing_rationale_count == 0`
- [ ] Every `integrity` value in `summary_metrics.json` is `0`
- [ ] No `SELECT` of `true_cause` outside `metrics/` — `grep -rn "true_cause" backend/revflow/` returns hits only under `metrics/`

**Honesty**

- [ ] All ten §5.6 invariants assert successfully
- [ ] No number in `frontend/` is hardcoded — no rupee literal, no percentage literal
- [ ] No `06_UIUX_RevFlow.md` placeholder value appears anywhere in source
- [ ] `addressable_coverage` is displayed beside `recovery_rate_realised`, never alone
- [ ] `b2b_receivable.recovery_rate_realised` renders as `—`, not `0%`
- [ ] README states plainly what is real and what is simulated

**Safety**

- [ ] `RAZORPAY_KEY_ID` starts `rzp_test_`; the startup assertion is present and tested
- [ ] `grep -riE "twilio|plivo|exotel|gupshup|msg91|karix|sendgrid|mailgun|smtplib|boto3" .` returns nothing outside `docs/`
- [ ] `git log --all --full-history -- "**/.env"` returns nothing
- [ ] No raw card data field exists in any schema (NFR-4)

**Completeness**

- [ ] All ten §7 endpoints respond; none returns a stub
- [ ] `contracts/enums.py` and `frontend/lib/contracts.ts` agree, asserted by a test
- [ ] Every enum value in §2 is either exercised by the dataset or documented as unreachable in Phase 0
- [ ] Exceptions screen shows ≥1 `stop` and ≥1 `escalate_to_human`
- [ ] All three ladder steps appear in one run's audit log
- [ ] Both a PTP pause and a PTP broken-promise escalation appear in one run's audit log
- [ ] All six modules have a clickable real audit example

**Document integrity**

- [ ] No document references a filename outside the §0.1 list
- [ ] Every FR/NFR ID cited in any document is defined in `04_SRS_RevFlow.md`
- [ ] Every section number cited cross-document resolves to a real section

---

*End of binding contracts. On any conflict between this document and another, this
document wins — and the conflict is a defect worth reporting.*
