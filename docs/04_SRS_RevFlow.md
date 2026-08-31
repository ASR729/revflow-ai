# RevFlow — Software Requirements Specification

**Document:** `04_SRS_RevFlow.md`
**Version:** 2.0 (rewritten for cross-document consistency)
**Status:** Binding for requirement identity. Subordinate to `00_CONTRACTS_RevFlow.md` on any technical value.
**Standard:** IEEE 830 conventions, adapted
**Project:** RevFlow — AI-Powered Revenue Recovery Orchestration
**Track:** Razorpay AI Buildathon, Track 03 — AI Revenue Recovery

---

> **Precedence.** This document is the single source of truth for **requirement
> identity**: what FR-1 through FR-36 and NFR-1 through NFR-9 mean, and nothing
> else may define or renumber them. It is *not* the source of truth for technical
> values. Every enum, constant, schema, formula, and endpoint referenced here is
> defined in `00_CONTRACTS_RevFlow.md`, and where this document and the contracts
> appear to differ, the contracts win. This split is deliberate: requirements
> change slowly and values change often, and a document that owns both drifts
> from itself.

---

## 1. Introduction

### 1.1 Purpose

This specification defines the functional and non-functional requirements for
RevFlow Phase 0 — the buildathon build. It exists so that an implementing agent
can determine, for any behaviour it is about to write, whether that behaviour is
required, forbidden, or out of scope, without inferring the answer.

The specification is written to be *checkable*. Each functional requirement is
phrased so that a reviewer can point at a line of code, a database row, or a test
and say whether the requirement is met. Requirements that could not be phrased
that way were either sharpened until they could, or moved to Section 9.

### 1.2 Scope

RevFlow ingests failed or stalled payment events across three revenue pipelines,
diagnoses why each one failed, decides what to do within a hard policy ceiling,
executes or simulates that action, and records every step in an append-only
ledger.

The three pipelines are `checkout_dropoff`, `subscription_failure`, and
`b2b_receivable` (`00_CONTRACTS_RevFlow.md` §2.1). The six product modules built
on top of them are enumerated in `01_PRD_RevFlow.md` §5 and mapped to runtime
components in `00_CONTRACTS_RevFlow.md` §1.1.

**In scope for Phase 0.** A batch-mode system operating on a synthetic dataset of
300 events, executing real payment retries through Razorpay Test Mode, simulating
all customer communication, and presenting results through a read-only dashboard.

**Out of scope for Phase 0.** Section 9 lists this explicitly. In summary: no
production merchant data, no real outbound messaging of any kind, no live voice
calls, no authentication, no multi-tenancy, no continuous or streaming operation.

### 1.3 Definitions, acronyms, abbreviations

The canonical vocabulary lives in `00_CONTRACTS_RevFlow.md` §1. The terms below
are the ones this document uses most, repeated here for readability only — the
contracts definition governs.

| Term | Meaning |
|---|---|
| **Pipeline** | One of the three `event_type` values. The dimension all metrics are keyed by. |
| **Module** | One of the six product features in `01_PRD_RevFlow.md` §5. A pitch-level unit, not a code unit. |
| **Component** | One of the six runtime Python packages in `05_System_Architecture_RevFlow.md` §3. |
| **Event** | One recoverable revenue item: an abandoned checkout, a failed charge, or an overdue invoice. |
| **Decision** | The `(action, ladder_step, rationale, rule_fired)` tuple the Policy Engine produces for one event on one pass. |
| **Hard stop** | A deterministic refusal to act, evaluated before any LLM call. See FR-6 and §3.1.1. |
| **Ceiling** | The set of bounds the LLM cannot exceed, enforced in plain Python. |
| **Simulated action** | Outreach copy written to the database and never transmitted. See FR-24, FR-28. |
| **PTP** | Promise-to-Pay. A customer's stated commitment to pay by a date. |
| **Ladder** | The B2B escalation sequence: `gentle_reminder` → `firm_reminder` → `flag_for_human`. |
| **NPCI** | National Payments Corporation of India. Its Technical/Business Decline split is descriptive framing only (`00_CONTRACTS_RevFlow.md` §2.2). |

### 1.4 References

Every document RevFlow depends on, and nothing else. This list is closed —
`00_CONTRACTS_RevFlow.md` §0.1 defines the complete set, and a reference to any
filename outside it is a defect.

| Document | Role relative to this SRS |
|---|---|
| `00_CONTRACTS_RevFlow.md` | Supplies every technical value this SRS refers to. Wins on conflict. |
| `01_PRD_RevFlow.md` | Supplies product intent and success metrics. Traced in §8. |
| `02_Teardown_RevFlow.md` | Supplies the market evidence that motivates FR-6, FR-13, FR-17, FR-18. |
| `03_Roadmap_RevFlow.md` | Supplies scope boundaries and the milestone table. |
| `05_System_Architecture_RevFlow.md` | Realises these requirements as components. |
| `06_UIUX_RevFlow.md` | Realises FR-28 through FR-31 as screens. |
| `07_Development_Plan_RevFlow.md` | Sequences these requirements as tasks. |
| `08_Audit_Report_RevFlow.md` | Records what changed between v1 and v2 of this document, and why. |

### 1.5 Overview

Section 2 describes the system in context. Section 3 states the functional
requirements, grouped by module, with the deterministic stopping rules stated
first because everything else is subordinate to them. Section 4 covers external
interfaces, Section 5 the non-functional requirements, Section 6 the system
models, Section 7 the compliance posture, Section 8 the traceability matrices,
and Section 9 the explicit exclusions.

---

## 2. Overall description

### 2.1 Product perspective

RevFlow is a new, self-contained system. It is not a component of, nor an
extension to, any existing product. It integrates with exactly one external
service — the Razorpay Test Mode API — and one LLM provider, and has no other
outbound network dependency. The absence of a messaging provider is architectural
and is enforced by test (FR-24, `00_CONTRACTS_RevFlow.md` §8.4).

Architecturally it is a modular monolith: a FastAPI backend over SQLite, with a
Next.js frontend that reads from it. The reasoning for that choice, rather than
services, is recorded in `05_System_Architecture_RevFlow.md` §7.

### 2.2 Product functions (summary)

The system detects recoverable revenue events, diagnoses each one's cause,
decides on an action within a fixed ceiling, executes real retries or writes
simulated outreach, tracks promises to pay, escalates B2B receivables through a
bounded ladder, and exposes the whole decision history through a read-only
dashboard. Section 3 specifies each of these.

### 2.3 User classes and characteristics

| Class | Description | Interaction |
|---|---|---|
| **Revenue operations analyst** | Primary user. Owns collections and recovery outcomes. Non-technical. | Reads the dashboard, works the exceptions queue. |
| **Finance / AR lead** | Owns the receivables ledger and customer relationships. | Reads B2B escalations, cares most about FR-17. |
| **Compliance reviewer** | Needs to establish that the system did not do anything it shouldn't. | Reads the audit trail. Primary consumer of NFR-1 and NFR-3. |
| **Buildathon judge** | Evaluates whether the claimed behaviour is real. | Reads the dashboard, clicks through to audit rows, reads the repository. |
| **Implementing agent** | Builds the system from this document set. | Reads all nine documents. Constrained by `00_CONTRACTS_RevFlow.md` §0.4. |

Phase 0 has no authentication and therefore no enforced role separation. All
users see the same read-only surface. This is a stated Phase 0 limitation, not an
oversight — see Section 9.

### 2.4 Operating environment

A single machine. Python 3.11+ with FastAPI and Uvicorn on the backend, SQLite as
the datastore, Node 18+ with Next.js and React on the frontend. Exact package
choices and the repository layout are fixed in `00_CONTRACTS_RevFlow.md` §9.
Browser support is current Chrome and Firefox at desktop widths; the dashboard is
a demo surface, not a responsive product.

### 2.5 Design and implementation constraints

The build is constrained in five ways that shape the requirements below.

**Zero marginal cost.** Every dependency must have a free tier sufficient for the
build. This bounds the LLM call budget (`LLM_CALL_BUDGET_PER_RUN = 90`) and is a
substantive reason Stage 3 of the policy engine exists at all — see
`03_Roadmap_RevFlow.md` §3.

**Test Mode only.** `RAZORPAY_KEY_ID` must match `^rzp_test_`, asserted at
startup with no override path (`00_CONTRACTS_RevFlow.md` §8.3). There is no
configuration that makes RevFlow touch live money in Phase 0.

**No messaging provider.** Not disabled, not stubbed behind a flag — absent. See
FR-24.

**Ten days.** The schedule in `03_Roadmap_RevFlow.md` §4 and
`07_Development_Plan_RevFlow.md` §5 is fixed, and the priority column in
`00_CONTRACTS_RevFlow.md` §11.1 is what gets cut if it slips.

**Determinism.** `RANDOM_SEED = 42` governs dataset generation, because NFR-8 and
the reproducibility requirement in `07_Development_Plan_RevFlow.md` (BUG-2) are
otherwise unassertable.

### 2.6 Assumptions and dependencies

RevFlow assumes the synthetic dataset is a fair enough proxy for the failure
distribution described in `02_Teardown_RevFlow.md` §1 that decisions made on it
would transfer — an assumption the system cannot itself validate, and which
Phase 1 exists to test. It assumes Razorpay Test Mode remains reachable, and
degrades to `outcome = api_error` rather than failing the run when it is not
(FR-15, `00_CONTRACTS_RevFlow.md` §8.3). It assumes an LLM provider free tier
remains available, and provides a `use_llm: false` offline path so the demo does
not depend on that assumption holding at the wrong moment
(`00_CONTRACTS_RevFlow.md` §7.2).

---

## 3. Specific requirements — functional

Each requirement carries a **priority** and a **verification method**. Priorities
are reproduced from `00_CONTRACTS_RevFlow.md` §11.1, which is the reconciliation
table — if a priority here disagrees with §11.1, §11.1 is correct and this is a
defect. Verification methods are `Test` (an automated test asserts it), `Inspect`
(a reviewer reads code or a database row), or `Demo` (visible in the running
system).

### 3.1 Module 1 & 2 — Root Cause Classifier and Policy Engine

This is the core of the system and the part that carries the product's central
claim. Everything in §3.2 through §3.7 is downstream of it.

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-1** | The system shall ingest events of all three `event_type` values from the synthetic dataset, validating each against the `events` schema before insert. Rows failing validation shall be rejected with a logged reason, never silently coerced. | Must | Test |
| **FR-2** | The system shall assign exactly one `cause` to every ingested event, using a deterministic `decline_code` → `cause` mapping first, and an LLM only for events whose code is absent or unmapped. | Must | Test |
| **FR-3** | The system shall record `cause_source` as `rule` or `llm` on every audit row, so the deterministic-versus-LLM split reported in `01_PRD_RevFlow.md` §9 is computed from data rather than asserted. | Should | Inspect |
| **FR-4** | The system shall compute per-cause precision and recall for the classifier by comparing assigned `cause` against the dataset's withheld `true_cause`, and expose the result at `GET /classifier-metrics`. `true_cause` shall not be readable by the classifier or the Policy Engine. | Must | Test |
| **FR-5** | The system shall select actions only from the closed five-value `action` enum. No other action value shall exist in the codebase, the database, or any LLM prompt's allow-list. | Must | Test |
| **FR-6** | The system shall apply every deterministic stopping rule in §3.1.1 **before** any LLM call is made for that event, such that an event caught by a hard stop consumes zero LLM calls. | Must | Test |
| **FR-7** | The system shall record a non-empty, human-readable `rationale` on every decision, naming the cause and the rule that authorised the action. A decision with an empty rationale shall be treated as a failed decision. | Must | Test |
| **FR-34** | The system shall resolve the action deterministically from the decision table in `00_CONTRACTS_RevFlow.md` §4.3 wherever a matching row exists, and shall reach the LLM only for events with no matching row. | Must | Test |

**On FR-4.** This requirement is the reason the dataset carries a withheld
`true_cause` column and the reason 12% of events are deliberately ambiguous
(`00_CONTRACTS_RevFlow.md` §6.3). Without the ambiguous subset, every event's
cause would be recoverable from its `decline_code` by table lookup, precision and
recall would both be 1.0 by construction, and the metric would measure nothing.
An implementing agent that generates a dataset where the mapping is total has
satisfied FR-2 and quietly destroyed FR-4.

**On FR-6.** The ordering is the requirement. "The LLM is instructed not to
retry revoked mandates" does not satisfy FR-6; "the code returns `stop` before
the LLM is constructed" does. `TEST-1` exists to assert exactly this, and
`llm_calls_used = 0` on a hard-stopped event is the assertion that cannot be
faked by a well-behaved model.

#### 3.1.1 Deterministic stopping rules (hard ceiling, non-negotiable)

These five rules run in plain Python, in this order, before Stage 4 is reachable.
The authoritative implementation specification is
`00_CONTRACTS_RevFlow.md` §4.2 (stage ordering) and §4.3 (rows 1–3); the constants
are in §4.1. Stated here because they are requirements, not just configuration.

| # | Rule | Constant | Outcome | `rule_fired` |
|---|---|---|---|---|
| 1 | Never act on an event whose cause is in the stop denylist. | `STOP_IF_CAUSE_IN` | `stop` / `withheld` | `hard_stop_cause_in_denylist` |
| 2 | Never exceed the retry ceiling. | `MAX_RETRIES` | `escalate_to_human` | `retry_ceiling_reached` |
| 3 | Never contact a customer more than the daily cap. | `MAX_CONTACTS_PER_CUSTOMER_PER_DAY` | `retry_later` | `contact_cap_reached` |
| 4 | Never retry inside the cooldown window. | `COOLDOWN_HOURS` | `retry_later` | `cooldown_active` |
| 5 | Never contact a customer under an active promise-to-pay. | `PTP_GRACE_DAYS` | `retry_later` / `paused` | `ptp_pause_active` |

`STOP_IF_CAUSE_IN` contains exactly `user_revoked` and `invoice_disputed`. Both
represent a customer who has already said no — one by cancelling a mandate, one by
contesting an invoice. `02_Teardown_RevFlow.md` §3 documents that the incumbent
tools have no equivalent of this rule, which is why it is stated as a requirement
rather than left to configuration.

**These five rules are fixed in every phase.** `03_Roadmap_RevFlow.md` Appendix A
commits to keeping them non-tunable even after per-merchant tuning arrives. A
system that can learn its own limits does not have limits.

### 3.2 Module 3a — Checkout Drop-off Recovery

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-8** | The system shall treat a checkout session with no successful payment after `CHECKOUT_SESSION_WINDOW_MINUTES` as abandoned. | Must | Test |
| **FR-9** | The system shall distinguish a session that failed at payment from one exited before any payment attempt, assigning a payment-failure cause only to the former. | Must | Test |
| **FR-10** | Where a `nudge` is generated for a checkout event, the system shall include a resumable checkout reference in the simulated copy. | Should | Demo |
| **FR-11** | The system shall not generate more than `MAX_CONTACTS_PER_CUSTOMER_PER_DAY` contacts for the same `customer_id` in the same day, counting across all pipelines rather than per pipeline. | Must | Test |
| **FR-33** | The system shall maintain a `contact_log` table recording every simulated contact, and shall enforce FR-11 by querying it rather than by in-memory counting. | Must | Test |

**On FR-11 and FR-33.** The cap counts per customer, not per pipeline. A customer
with both an abandoned checkout and an overdue invoice receives one contact, not
two. This is the requirement that makes the "harassment cost" metric in
`00_CONTRACTS_RevFlow.md` §5.5 meaningful, and enforcing it in memory rather than
against `contact_log` would make it unverifiable after the run — which is why
FR-33 exists as a separate requirement rather than as an implementation note.

### 3.3 Module 3b — Subscription and Mandate Recovery

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-12** | The system shall classify subscription charge failures across the applicable causes in `00_CONTRACTS_RevFlow.md` §2.2, distinguishing recoverable technical failures from terminal mandate states. | Must | Test |
| **FR-13** | The system shall never issue a payment retry for an event whose cause is `mandate_expired` or `user_revoked`. `mandate_expired` shall route to re-authorisation outreach; `user_revoked` shall route to `stop`. | Must | Test |
| **FR-14** | The system shall schedule deferred retries according to `RETRY_BACKOFF_HOURS`, indexed by `retry_count`, and shall never schedule an attempt that violates `COOLDOWN_HOURS` or `MAX_RETRIES`. | Must | Test |
| **FR-15** | The system shall attribute every retry attempt to the rule that authorised it via a non-null `rule_fired`, and shall record `api_error` as the outcome when an external call fails rather than treating the attempt as not having happened. | Must | Test |

**On FR-13.** This is the requirement that distinguishes RevFlow from
retry-oriented dunning tools, and it is worth being precise about why. Retrying an
expired mandate cannot succeed — the authorisation is gone — so each attempt buys
nothing and costs the merchant a decline on their rail. Retrying a revoked mandate
is worse than useless: the customer has explicitly withdrawn permission.
`00_CONTRACTS_RevFlow.md` §4.3 rows 1 and 15 encode the distinction, and
`TEST-1` asserts it.

### 3.4 Module 5 — B2B Receivables Chaser

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-16** | The system shall assign a `ladder_step` to overdue invoices based on invoice age, using `LADDER_GENTLE_AFTER_DAYS`, `LADDER_FIRM_AFTER_DAYS`, and `LADDER_FLAG_AFTER_DAYS` as thresholds, and shall advance by at most one step per decision. | Must | Test |
| **FR-17** | The system shall never auto-escalate a receivable beyond `flag_for_human`. No path shall exist to legal action, collections referral, or credit reporting. | Must | Inspect |
| **FR-18** | The system shall suspend ladder advancement for any invoice covered by an active promise-to-pay. | Must | Test |

**On FR-16 — monotonicity.** The age thresholds determine the *highest step an
invoice may currently occupy*, not the step it is assigned. An invoice sitting at
`gentle_reminder` that crosses 45 days advances to `firm_reminder`, not to
`flag_for_human`. The reason is that the ladder's value is the sequence: a
customer who receives a firm reminder with no prior gentle one experiences the
system as arbitrary. `00_CONTRACTS_RevFlow.md` §4.3 states the rule; the dataset
seeds starting steps one below the age ceiling (§6.6) so a single run exercises
all three steps and the behaviour is demonstrable rather than merely specified.

**On FR-17.** Verification is by inspection rather than test because the
requirement is about *absence*. There is no legal-escalation code path to
exercise, and the check is that `flag_for_human` is the terminal value of the
`ladder_step` enum with nothing beyond it.

### 3.5 Module 4 — Promise-to-Pay Tracker

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-19** | The system shall detect promise-to-pay commitments in customer reply text and extract the promised date, using regex first and an LLM only where commitment language is present but no date parses. The detection source shall be recorded. | Must | Test |
| **FR-20** | The system shall pause all outreach for an event under an active promise until `promised_date + PTP_GRACE_DAYS`, recording `outcome = paused` and `rule_fired = ptp_pause_active` on each pass during the pause. | Must | Test |
| **FR-21** | On a broken promise, the system shall resume at exactly one step above the `ladder_step` held at pause time, and shall never resume at `gentle_reminder`. | Must | Test |

**On FR-21.** A system that restarts the ladder after a broken promise teaches
customers that promising is free. Resuming one step *up* is the behaviour a
competent human collections operator has, and it is the specific mechanic
`02_Teardown_RevFlow.md` §4 identifies as unoccupied whitespace. The
implementation depends on `ptp_commitments.ladder_step_at_pause`, which exists
solely to make FR-21 assertable after the fact.

### 3.6 Module 3c — Hinglish Voice Recovery

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-22** | The system shall generate outreach copy in a Hinglish register, with tone calibrated to cause — apologetic where the failure was the rail's fault, neutral where it was the payer's. | Should | Demo |
| **FR-23** | The system shall produce at least one audio artefact from a generated voice script using a local, offline text-to-speech path. | Should | Demo |
| **FR-24** | The system shall not transmit any real communication through any channel. No messaging, telephony, or email provider shall be present as a dependency, and this shall be verified by a repository-wide check rather than by inspection alone. | Must | Test |
| **FR-25** | Live outbound voice, when introduced, shall require per-customer recorded consent captured before the first call. | Deferred | — |

**On FR-24.** The verification method matters. `00_CONTRACTS_RevFlow.md` §8.4
lists the prohibited packages and specifies a grep executed as a P0 test, because
"we did not integrate a messaging provider" is a claim that decays the moment
someone adds a convenience dependency. The test makes the absence durable.

**On FR-25.** Marked `Deferred`, not `Must` or `Won't`. It is a real requirement
with a real owner in Phase 2 (`03_Roadmap_RevFlow.md` Appendix A), and it is
recorded here so that the consent obligation is visible from the start rather
than discovered when live messaging is switched on. Nothing in Phase 0 implements
it, and nothing in Phase 0 needs to, because FR-24 makes it inapplicable.

### 3.7 Module 6 — Audit Ledger and Dashboard

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **FR-26** | The system shall append exactly one `audit_log` row per decision, carrying event reference, cause, `cause_source`, action, `ladder_step`, rationale, `rule_fired`, `llm_calls_used`, outcome, and timestamp. Audit rows shall never be updated or deleted. | Must | Test |
| **FR-27** | The system shall write the audit row **before** executing or simulating the action, so that a crash mid-execution leaves a record of intent rather than silence. | Must | Test |
| **FR-28** | The system shall label every simulated action as simulated in the database, the API response, and every UI surface that displays it. A simulated action shall never be presentable as a completed one. | Must | Test |
| **FR-29** | The system shall display the metric set defined in `00_CONTRACTS_RevFlow.md` §5, including `addressable_coverage` wherever a recovery rate is shown. | Must | Demo |
| **FR-30** | The audit trail view shall be sortable and filterable by pipeline, action, cause, and outcome. | Should | Demo |
| **FR-31** | The system shall provide an exceptions view listing every event whose action was `stop` or `escalate_to_human`, with no omissions, and shall show for each the rule that produced it. | Must | Test |
| **FR-32** | The system shall scope every batch to a `batch_runs` row with a unique `run_id`, and shall retain prior runs rather than overwriting them. | Must | Test |
| **FR-35** | The system shall expose `POST /run-batch` to trigger a run, returning 202 immediately, executing in the background, and returning 409 if a run is already in progress. | Must | Test |
| **FR-36** | The system shall expose the active policy constants read-only at `GET /config`, so displayed thresholds are read from the engine rather than duplicated in the frontend. | Should | Test |

**On FR-27 — write-before-execute.** The ordering is the audit guarantee. If the
action is executed first and the row written after, then any failure between the
two produces an action with no record — precisely the case an auditor cares about
most. Writing intent first means the worst case is a recorded decision with an
unresolved outcome, which is honest and detectable.

**On FR-29 and `addressable_coverage`.** A recovery rate shown without its
coverage figure is misleading, because only `retry_now` actions can realise money
(`00_CONTRACTS_RevFlow.md` §5.1). A headline "recovery rate" computed over all
at-risk value would imply the system recovers revenue it never had a mechanism to
touch. Pairing the two is what makes the number defensible under questioning, and
it is why the pairing is a requirement rather than a presentation preference.

**On FR-31 — "no omissions".** The exceptions view is where the product's
restraint becomes visible. If it filters, paginates silently, or drops rows, the
claim in `01_PRD_RevFlow.md` §5.6 that every withheld action is inspectable
becomes false. The test asserts that the exceptions count equals the count of
`stop` plus `escalate_to_human` rows in the audit log for that run.

**On FR-36.** Duplicating `MAX_RETRIES` as a literal in a React component is the
most likely way for the dashboard to display a threshold the engine no longer
uses. `GET /config` removes the reason to duplicate it.

---

## 4. External interface requirements

### 4.1 User interfaces

Three screens and one drawer, specified in full in `06_UIUX_RevFlow.md`: a
Dashboard (metrics), an Audit Trail (the ledger), an Exceptions view (FR-31), and
a Decision Drawer that opens from any audit row.

**The frontend is a pure read layer.** It issues no writes other than the
`POST /run-batch` trigger (FR-35), which is a run control rather than a data
mutation. No screen offers a retry button, an override, an edit, or an approve
action. This follows from FR-26: a UI that can alter a decision after the fact
would make the ledger's append-only property a property of the database only, not
of the system. `06_UIUX_RevFlow.md` §7 states the same constraint for error
states, which must not offer a retry affordance.

Every number displayed shall be fetched from the API. No rupee value, count, or
percentage shall appear as a literal in frontend source (NFR-7). The illustrative
figures in `06_UIUX_RevFlow.md` wireframes are layout placeholders and are
explicitly labelled as such; treating one as a target is a defect.

### 4.2 API interfaces

Ten endpoints, specified exactly in `00_CONTRACTS_RevFlow.md` §7 — request shape,
response shape, and status codes. This section states only their purpose and the
requirement each serves.

| Endpoint | Purpose | Requirement |
|---|---|---|
| `GET /health` | Liveness. | — |
| `POST /run-batch` | Trigger a run; 202 + background execution; 409 if one is active. | FR-35 |
| `GET /runs` | List prior runs. | FR-32 |
| `GET /metrics` | The `summary_metrics.json` payload. | FR-29 |
| `GET /classifier-metrics` | Per-cause precision and recall. | FR-4 |
| `GET /audit-log` | The ledger, filterable and sortable. | FR-26, FR-30 |
| `GET /exceptions` | Every `stop` and `escalate_to_human`. | FR-31 |
| `GET /events/{event_id}` | One event with its decision history. `true_cause` omitted. | FR-4 |
| `GET /config` | Active policy constants, read-only. | FR-36 |
| `POST /webhook` | Razorpay Test Mode callback receiver. | FR-15 |

`00_CONTRACTS_RevFlow.md` §7.11 lists endpoints that deliberately **do not
exist**, including any that would mutate a decision. An agent that adds a
`POST /retry/{event_id}` has violated FR-26 regardless of how the handler is
written.

`GET /events/{event_id}` omits `true_cause` from its response. This is a
requirement of FR-4, not a convenience: an endpoint that returns the withheld
label makes the classifier's ground truth reachable from the frontend, and from
there the temptation to display "correct/incorrect" per row leaks the answer key
into the surface being evaluated.

### 4.3 Hardware interfaces

None. Audio artefacts under FR-23 are written to disk as files; no audio device is
accessed and no telephony hardware exists.

### 4.4 Communication interfaces

Exactly two outbound: HTTPS to the Razorpay Test Mode API, and HTTPS to one LLM
provider endpoint. Both are wrapped in adapters
(`00_CONTRACTS_RevFlow.md` §8.1, §8.3) that must return a typed failure rather
than raise, so an unreachable dependency degrades the run instead of ending it.

There is no third outbound interface, and this is the requirement rather than the
current state. Adding one — a messaging provider, a webhook to an external
service, a telemetry endpoint — violates FR-24.

---

## 5. Non-functional requirements

| ID | Requirement | Priority | Verify |
|---|---|---|---|
| **NFR-1** | **Auditability.** Every action taken or withheld shall be reconstructible from the audit log alone, without reference to application logs or the source code. | Must | Inspect |
| **NFR-2** | **Boundedness.** The policy ceiling shall be enforced in code, not in prompt text. It shall be impossible for any LLM output to produce an action outside the closed enum or to bypass a §3.1.1 rule. | Must | Test |
| **NFR-3** | **Explainability.** Every decision shall carry a rationale a non-technical operator can read and act on, naming the cause and the authorising rule in plain language. | Must | Inspect |
| **NFR-4** | **Data protection.** No raw card data shall be stored in any table. Secrets shall be read only through the environment layer, never logged — not even truncated — and `.env` shall never appear in git history at any point. | Must | Test |
| **NFR-5** | **Consent.** No communication channel requiring consent shall be exercised in Phase 0. FR-24 makes this structurally true rather than procedurally enforced. | Must | Test |
| **NFR-6** | **Latency.** A single event's decision, excluding external API round-trips, shall complete within `DECISION_LATENCY_BUDGET_MS`. | Should | Test |
| **NFR-7** | **Metric honesty.** Every displayed figure shall be computed from stored rows. No hardcoded, illustrative, or hand-tuned value shall appear in frontend or backend source. Where a rate is undefined for lack of an addressable denominator, it shall render as null rather than as zero. | Must | Test |
| **NFR-8** | **Unattended reproducibility.** A full 300-event batch shall run to completion from a wiped database with no human intervention, and two such runs shall be structurally identical under `RANDOM_SEED`. | Must | Test |
| **NFR-9** | **Phase 1 readiness.** The Phase 0 schema and adapter boundaries shall admit real merchant data and real messaging without redesign of the policy engine. | Should | Inspect |

**On NFR-2.** This is the non-functional requirement the product is built around,
and the distinction it draws is the one most easily lost. A prompt that says "you
may only choose from retry_now, nudge, stop" is a request. A validator that
rejects any response outside that set and defaults to `escalate_to_human` is a
bound. `TEST-3` asserts the difference by feeding the validator a response the
prompt forbids — `"delete_customer"`, an empty string, malformed JSON, a timeout —
and requiring `escalate_to_human` with
`rule_fired = llm_output_rejected_defaulted` in every case. The system fails
toward caution, and the test proves the direction of failure.

**On NFR-7 and the null rate.** `b2b_receivable` has no `retry_now` row anywhere
in `00_CONTRACTS_RevFlow.md` §4.3, so no B2B event can realise recovered money
through a payment rail, so its realised recovery rate has a zero denominator. The
requirement is that this renders as `—` and not as `0%`. Zero percent asserts that
the system tried and failed; null states correctly that the system has no
mechanism here and is not claiming one. This distinction survives a judge asking
"so what does this number actually mean?" — the earlier version of the metric set
did not.

**On NFR-4 and git history.** "Not committed" is insufficient; the requirement is
"never committed", checked with
`git log --all --full-history -- "**/.env"`. A secret removed in a later commit is
still a leaked secret, and a repository submitted for judging is a repository whose
history is readable.

---

## 6. System models

### 6.1 High-level data flow

```text
  Synthetic dataset (300 events, RANDOM_SEED=42)
            │
            ▼
  [1] Ingestion ──────────────► events table (run-scoped by run_id)
            │
            ▼
  [2] Root Cause Classifier
        rules first (decline_code → cause)
        LLM only for unmapped / ambiguous
            │
            ▼
  [3] Policy Engine
        Stage 1  hard stop            ─┐
        Stage 2  guards                │ no network I/O
        Stage 3  deterministic table  ─┘
        Stage 4  bounded LLM           (minority of events)
            │
            ▼
  [4] audit_log  ◄── written BEFORE execution (FR-27)
            │
            ▼
  [5] Action Executor
        retry_now  ──► Razorpay Test Mode  (real)
        nudge      ──► simulated_actions   (never transmitted)
        escalate   ──► escalations
        retry_later / stop ──► no outbound effect
            │
            ▼
  [6] Metrics ──► GET /metrics ──► Dashboard (read-only)
```

The single most important property of this diagram is that step 4 precedes
step 5, and that steps 1 through 3 can complete with the network unavailable.

### 6.2 Core data entities

Seven tables, specified with full column lists, types, constraints, and foreign
keys in `00_CONTRACTS_RevFlow.md` §3. Summarised here for orientation only.

| Table | Holds | Notes |
|---|---|---|
| `batch_runs` | One row per run | FR-32. Parent of everything else. |
| `events` | The recoverable items | Carries withheld `true_cause`, readable only by the FR-4 metrics path. |
| `audit_log` | One row per decision | Append-only. FR-26, FR-27. |
| `simulated_actions` | Outreach copy | Never transmitted. FR-24, FR-28. |
| `escalations` | Human review queue | FR-17 terminus. |
| `contact_log` | Contact history | Backs the FR-11 cap. FR-33. |
| `ptp_commitments` | Promises to pay | Carries `ladder_step_at_pause` for FR-21. |

All monetary values are stored as integer paise. No float is used for money
anywhere in the system, and display formatting is applied only at the presentation
layer (`00_CONTRACTS_RevFlow.md` §10.2).

**Data lifecycle.** Each run inserts a new `batch_runs` row and scopes its events
to that `run_id`. Nothing is truncated. The v1 architecture specified truncating
`events` while appending to `audit_log`, which orphans every foreign key from the
prior run and makes the ledger unreadable one run later —
`00_CONTRACTS_RevFlow.md` §3.9 replaces it, and `08_Audit_Report_RevFlow.md`
records why.

### 6.3 Use case summary

| ID | Actor | Use case | Requirements |
|---|---|---|---|
| UC-1 | Analyst | Trigger a recovery batch and watch it complete | FR-35, FR-32, NFR-8 |
| UC-2 | Analyst | Read recovery performance by pipeline | FR-29, NFR-7 |
| UC-3 | Analyst | Inspect why one event was decided as it was | FR-7, FR-26, NFR-3 |
| UC-4 | Analyst | Work the exceptions queue | FR-31, FR-17 |
| UC-5 | Compliance reviewer | Establish that no revoked mandate was retried | FR-6, FR-13, NFR-1 |
| UC-6 | Compliance reviewer | Establish that nothing was actually transmitted | FR-24, FR-28, NFR-5 |
| UC-7 | AR lead | Confirm a promised invoice is paused, not chased | FR-18, FR-20 |
| UC-8 | AR lead | Confirm a broken promise escalated rather than restarted | FR-21 |
| UC-9 | Judge | Verify a displayed number traces to a stored row | NFR-7, FR-26 |

UC-5 and UC-6 are the two that most product demos cannot service, and they are
serviceable here specifically because of the FR-27 ordering and the FR-28 labelling
requirement.

---

## 7. Legal, regulatory, and compliance posture

RevFlow Phase 0 processes no personal data belonging to a real person. The dataset
is synthetic and generated locally under `RANDOM_SEED`, so DPDP Act obligations
concerning notice, consent, and data principal rights do not attach to Phase 0
operation. This is a consequence of scope, not of compliance work performed, and
the document says so rather than implying a review that has not happened.

No card data is stored, transmitted, or logged, so PCI DSS scope does not attach
either. Card details never reach RevFlow: retries execute against Razorpay Test
Mode using tokens and order references held by Razorpay (NFR-4).

TRAI's commercial communication rules — DND registry, consent registration,
sender-ID and template registration — govern outbound SMS and voice in India. They
do not bind Phase 0 because Phase 0 transmits nothing (FR-24, NFR-5). They bind
Phase 2 completely, and `03_Roadmap_RevFlow.md` Appendix A records that consent
capture, provider onboarding, and DPDP review all land there together and none of
them are small.

The requirement pair FR-17 and FR-25 exists for a reason worth stating plainly. A
system that can autonomously escalate a debt toward legal action, or place a voice
call without recorded consent, creates liability for the merchant that no
efficiency gain offsets. RevFlow's ceiling stops at `flag_for_human` — a queue a
person reads — and that limit is a design commitment carried through every phase
rather than a Phase 0 convenience.

---

## 8. Traceability

### 8.1 SRS section → PRD section

Reproduced from `00_CONTRACTS_RevFlow.md` §11.3. The v1 version of this matrix
pointed at "PRD Section 4.1–4.7", where PRD §4 is *Non-Goals* and §4.7 does not
exist. Corrected:

| SRS section | Module | PRD reference |
|---|---|---|
| §3.1 Core Engine | 1, 2 | `01_PRD_RevFlow.md` §5.1, §5.2 |
| §3.2 Checkout Drop-off | 3 | `01_PRD_RevFlow.md` §5.3 |
| §3.3 Subscription + Mandate | 3 | `01_PRD_RevFlow.md` §5.3, US-4, US-5 |
| §3.4 B2B Receivables | 5 | `01_PRD_RevFlow.md` §5.5, US-6 |
| §3.5 PTP Tracker | 4 | `01_PRD_RevFlow.md` §5.4, US-7 |
| §3.6 Hinglish Voice | 3 | `01_PRD_RevFlow.md` §5.3, §4 (non-goal boundary) |
| §3.7 Audit / Dashboard | 6 | `01_PRD_RevFlow.md` §5.6, §7 (US-1, US-8), §9 |
| §5 Non-functional | — | `01_PRD_RevFlow.md` §3, §9 |
| §7 Compliance | — | `01_PRD_RevFlow.md` §4, §12 |

### 8.2 Requirement → user story

Every P0 requirement traces to at least one user story in
`01_PRD_RevFlow.md` §7, and every user story traces back. Requirements with no
story are infrastructure and are marked as such.

| Requirement | User story |
|---|---|
| FR-1 | US-1 |
| FR-2, FR-3, FR-4 | US-2 |
| FR-5 | US-5 (via NFR-2) |
| FR-6 | US-3 |
| FR-7 | US-1, US-3 |
| FR-8, FR-9, FR-10 | *Infrastructure for module 3; no dedicated story* |
| FR-11, FR-33 | US-8 (contact restraint is visible as simulated-action count) |
| FR-12 | US-2 |
| FR-13 | US-3, US-4 |
| FR-14, FR-15 | US-5 |
| FR-16, FR-17 | US-6 |
| FR-18, FR-19, FR-20, FR-21 | US-7 |
| FR-22, FR-23 | *No dedicated story; P1 demo surface* |
| FR-24 | US-8 |
| FR-25 | *Deferred; no Phase 0 story* |
| FR-26, FR-29, FR-32, FR-35 | US-1 |
| FR-27 | US-1 (audit completeness) |
| FR-28 | US-8 |
| FR-30 | *P1 usability; no dedicated story* |
| FR-31 | US-3 |
| FR-34 | US-5 |
| FR-36 | US-5 (thresholds stated out loud come from the engine) |
| NFR-2 | US-5 |
| NFR-5 | US-4 |
| NFR-7 | US-9 |

### 8.3 Requirement → contract section

Where to find the technical values that implement each requirement. This is the
column an implementing agent should follow rather than inferring values.

| Requirement | Contract section |
|---|---|
| FR-1 | §2.1, §3.2, §6 |
| FR-2 | §2.2, §8.2 |
| FR-3 | §2.7, §3.3 |
| FR-4 | §5.7, §6.3, §7.5, §7.8 |
| FR-5 | §2.3 |
| FR-6 | §4.1, §4.2 Stage 1, §4.3 rows 1–2 |
| FR-7 | §3.3 |
| FR-8 | §4.1 `CHECKOUT_SESSION_WINDOW_MINUTES` |
| FR-9 | §2.2, §6.2 |
| FR-10 | §3.4 |
| FR-11 | §4.1 `MAX_CONTACTS_PER_CUSTOMER_PER_DAY`, §4.2 Stage 2d |
| FR-12 | §2.2, §6.2 |
| FR-13 | §4.3 rows 1, 15 |
| FR-14 | §4.1 `MAX_RETRIES`, `COOLDOWN_HOURS`, `RETRY_BACKOFF_HOURS` |
| FR-15 | §2.6, §8.3 |
| FR-16 | §4.1 ladder constants, §4.3 rows 17–20 |
| FR-17 | §2.4 |
| FR-18 | §4.4 |
| FR-19 | §4.4 step 1, §3.7 |
| FR-20 | §4.4 steps 2–3 |
| FR-21 | §4.4 step 4, §3.7 `ladder_step_at_pause` |
| FR-22 | §2.9, §3.4 |
| FR-23 | §8.4 |
| FR-24 | §8.4 |
| FR-25 | — (deferred) |
| FR-26 | §3.3 |
| FR-27 | §3.9, §4.2 |
| FR-28 | §2.5 `simulated`, §3.4 |
| FR-29 | §5.2–5.6 |
| FR-30 | §7.6 |
| FR-31 | §7.7 |
| FR-32 | §3.1, §3.9 |
| FR-33 | §3.6 |
| FR-34 | §4.3 |
| FR-35 | §7.2 |
| FR-36 | §7.9, §4.1 |
| NFR-1 | §3.3, §3.9 |
| NFR-2 | §4.2, §8.1 |
| NFR-3 | §3.3 `rationale` |
| NFR-4 | §10.1 |
| NFR-5 | §8.4 |
| NFR-6 | §4.1 `DECISION_LATENCY_BUDGET_MS` |
| NFR-7 | §5.1, §5.3, §5.6 |
| NFR-8 | §4.1 `RANDOM_SEED`, §6.8 |
| NFR-9 | §8.1, §8.3, §8.4 (adapter boundaries) |

### 8.4 The four guardrail requirements

Four tests are non-negotiable regardless of what else slips
(`00_CONTRACTS_RevFlow.md` §11.4, `07_Development_Plan_RevFlow.md` §3.6). Each
maps to the requirement it makes real.

| Test | Asserts | Requirement |
|---|---|---|
| **TEST-1** | `user_revoked` and `invoice_disputed` → `stop`, `llm_calls_used = 0` | FR-6, FR-13, NFR-2 |
| **TEST-2** | `retry_count >= MAX_RETRIES` → `escalate_to_human` | FR-14 |
| **TEST-3** | Invalid, empty, malformed, or timed-out LLM output → `escalate_to_human` | NFR-2, FR-5 |
| **TEST-5** | 300 events, fresh database, unattended, all §5.6 invariants hold | NFR-8, NFR-7 |

**TEST-1 is the most important test in the project.** It is the executable form of
the restraint claim, and if it does not pass, FR-6 is unevidenced and no other
completed work compensates. `02_Teardown_RevFlow.md` §4 stakes the product's
differentiation on precisely this behaviour.

---

## 9. Explicitly out of scope for Phase 0

Stated as exclusions rather than omissions, so that an implementing agent
encountering any of the following knows it is a boundary and not a gap. Adding any
item here is scope expansion, not completion.

**Real outbound communication of any kind.** No SMS, WhatsApp, email, or voice
call is transmitted. No messaging, telephony, or email provider is a dependency
(FR-24, `00_CONTRACTS_RevFlow.md` §8.4).

**Live payment processing.** Test Mode only, asserted at startup with no override
(`00_CONTRACTS_RevFlow.md` §8.3).

**Real merchant data.** The dataset is synthetic and locally generated. There is
no import path, no CSV upload, and no merchant connector.

**Authentication, authorisation, and multi-tenancy.** No login, no roles, no
per-merchant data isolation. The dashboard is open on localhost. Phase 1 work.

**Continuous or streaming operation.** RevFlow runs as a batch triggered by
`POST /run-batch`. There is no scheduler, no queue worker, no cron, and no
long-lived consumer.

**Runtime-editable policy.** The constants in `00_CONTRACTS_RevFlow.md` §4.1 are
module-level and read-only at runtime. `GET /config` reads them; nothing writes
them. Per-merchant tuning is Phase 3, and the §3.1.1 hard stops remain
non-tunable in every phase.

**Learned or adaptive thresholds.** No model is trained, fine-tuned, or updated
from outcomes. The LLM is used for classification of ambiguous causes, action
selection within a closed allow-list, and PTP date extraction — nothing else.

**Live Hinglish voice calls.** FR-23 produces an offline audio artefact from a
local TTS path. Placing a call requires FR-25 consent capture and TRAI compliance,
both Phase 2.

**Payment method optimisation, dynamic routing, and pricing.** RevFlow decides
*whether and when* to attempt recovery. It does not choose rails, reorder payment
methods, or alter amounts.

**Dispute and chargeback handling.** `invoice_disputed` is a hard stop, which is
the entirety of RevFlow's dispute behaviour: it stops and hands off.

**Mobile and responsive layouts.** Desktop widths only
(`06_UIUX_RevFlow.md` §2).

**Internationalisation beyond the three `locale` values.** `en`, `hi`, and
`hinglish` (`00_CONTRACTS_RevFlow.md` §2.9). No other locale, currency, or
regional payment rail.

---

**Cross-references used:** `00_CONTRACTS_RevFlow.md` §1, §1.1, §2.1–2.9, §3.1–3.9,
§4.1–4.4, §5.1–5.7, §6.2, §6.3, §6.8, §7, §7.2, §7.5–7.9, §7.11, §8.1–8.4, §9,
§10.1, §10.2, §11.1, §11.3, §11.4; `01_PRD_RevFlow.md` §3, §4, §5.1–5.6, §7, §9,
§12, US-1–US-9; `02_Teardown_RevFlow.md` §1, §3, §4;
`03_Roadmap_RevFlow.md` §3, §4, Appendix A; `05_System_Architecture_RevFlow.md`
§3, §7; `06_UIUX_RevFlow.md` §2, §7; `07_Development_Plan_RevFlow.md` §3.6, §5;
`08_Audit_Report_RevFlow.md`. All resolve.
