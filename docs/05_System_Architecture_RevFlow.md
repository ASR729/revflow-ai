# RevFlow — System Architecture

**Document:** `05_System_Architecture_RevFlow.md`
**Version:** 2.0 (rewritten for cross-document consistency)
**Status:** Binding for component boundaries. Subordinate to `00_CONTRACTS_RevFlow.md` on any technical value.
**Project:** RevFlow — AI-Powered Revenue Recovery Orchestration
**Track:** Razorpay AI Buildathon, Track 03 — AI Revenue Recovery

---

> **Precedence.** This document owns **component boundaries and data flow** — what
> the runtime pieces are, what each is allowed to do, and in what order they run.
> It does not own enums, schemas, constants, endpoint shapes, or formulas; those
> live in `00_CONTRACTS_RevFlow.md` and win on conflict. Requirement identity
> (FR-*/NFR-*) belongs to `04_SRS_RevFlow.md`.

---

## 1. Introduction

### 1.1 Purpose

This document describes how RevFlow is structured at runtime: the six components,
the order they execute in, what crosses the boundary between them, and which
decisions were made deliberately rather than by default. It exists so that an
implementing agent placing a piece of logic knows which component owns it.

### 1.2 Architectural goals

Derived from `04_SRS_RevFlow.md` §5. Each goal names the non-functional
requirement it serves and the architectural mechanism that delivers it — a goal
without a mechanism is an aspiration.

| Goal | NFR | Mechanism |
|---|---|---|
| Auditability | NFR-1 | A single write path (`db/ledger.py`) for audit rows; append-only; written before execution. |
| Boundedness | NFR-2 | Stages 1–3 of the Policy Engine are pure Python with no network I/O; Stage 4's output is validated in code against a closed enum. |
| Explainability | NFR-3 | `rationale` and `rule_fired` are non-null columns, not optional metadata. |
| Honest metrics | NFR-7 | Metrics are a component (`metrics/`) that reads the ledger. The frontend has no arithmetic. |
| Reproducibility | NFR-8 | Dataset generation is seeded; runs are scoped by `run_id` and never overwrite. |
| Phase 1 readiness | NFR-9 | External access is confined to two adapters, so swapping Test Mode for live, or absent-messaging for real messaging, touches no decision logic. |

### 1.3 Architectural constraints

Four constraints shaped the structure more than any preference did.

**No live outbound communication is permitted** (`04_SRS_RevFlow.md` §7, FR-24).
The consequence is stronger than a feature flag: the Action Executor must be
*physically unable* to reach a messaging provider. `executor/simulated_comms.py`
therefore contains no HTTP client of any kind, and
`00_CONTRACTS_RevFlow.md` §8.4 lists the packages whose presence anywhere in the
repository fails a test.

**Zero marginal cost** (`03_Roadmap_RevFlow.md` §3). SQLite rather than managed
Postgres, a free-tier LLM, local hosting. This is also why Stage 3 exists — see
§3.3.

**Test Mode only** (`00_CONTRACTS_RevFlow.md` §8.3). `adapters/razorpay_client.py`
asserts `^rzp_test_` at import and offers no override.

**Ten days, one builder.** This is the constraint behind the modular monolith
decision in §7.1, and it is worth naming as a constraint rather than presenting
the outcome as architecturally ideal in the abstract.

---

## 2. High-level architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        EVENT SOURCES                            │
│   Razorpay Test Mode webhooks   │   Synthetic dataset (batch)    │
│   POST /webhook                 │   scripts/generate_dataset.py  │
└──────────────────┬──────────────┴────────────┬──────────────────┘
                   └──────────────┬────────────┘
                                  ▼
        ┌─────────────────────────────────────────────┐
        │  1. EVENT INGESTION                         │  ingestion/
        │  Normalises both sources into one Event     │  Validates against
        │  shape. Scopes the batch to a run_id.       │  the events schema
        │  FR-1, FR-32                                │  before insert
        └─────────────────────┬───────────────────────┘
                              ▼
        ┌─────────────────────────────────────────────┐
        │  2. ROOT CAUSE CLASSIFIER                   │  classifier/
        │  Rules first: decline_code → cause          │  LLM touched only
        │  LLM only where the code is unmapped        │  by the ambiguous
        │  FR-2, FR-3, FR-4                           │  subset (~12%)
        └─────────────────────┬───────────────────────┘
                              ▼
        ┌─────────────────────────────────────────────┐
        │  3. POLICY ENGINE  ── the architectural core │  policy/
        │  ┌───────────────────────────────────────┐  │
        │  │ Stage 1  hard stops          no I/O   │  │  Stages 1–3 are
        │  │ Stage 2  guards              DB reads │  │  pure Python.
        │  │ Stage 3  deterministic table lookup   │  │  Stage 4 is
        │  │ Stage 4  bounded LLM         network  │  │  reached by a
        │  └───────────────────────────────────────┘  │  minority of
        │  FR-5, FR-6, FR-7, FR-34, NFR-2             │  events.
        └─────────────────────┬───────────────────────┘
                              ▼
        ┌─────────────────────────────────────────────┐
        │  4. AUDIT LEDGER  ── written BEFORE step 5  │  db/ledger.py
        │  Append-only. One row per decision.         │  The ONLY audit
        │  FR-26, FR-27, NFR-1                        │  write path.
        └─────────────────────┬───────────────────────┘
                              ▼
        ┌─────────────────────────────────────────────┐
        │  5. ACTION EXECUTOR  (channel router)       │  executor/
        │  ┌──────────┬────────────┬───────────────┐  │
        │  │ REAL     │ SIMULATED  │ NEITHER       │  │
        │  │ retry_now│ nudge      │ retry_later   │  │
        │  │ Razorpay │ DB write   │ escalate      │  │
        │  │ Test Mode│ only, no   │ stop          │  │
        │  │ API      │ HTTP client│               │  │
        │  └──────────┴────────────┴───────────────┘  │
        │  FR-15, FR-24, FR-28                        │
        └─────────────────────┬───────────────────────┘
                              ▼
        ┌─────────────────────────────────────────────┐
        │  6. API + DASHBOARD                         │  api/, metrics/,
        │  Ten endpoints. Metrics computed from the    │  frontend/
        │  ledger. Frontend is a pure read layer.      │
        │  FR-29, FR-30, FR-31, FR-36, NFR-7          │
        └─────────────────────────────────────────────┘
```

**Cross-cutting: the Promise-to-Pay Tracker** (`ptp/`) is not a stage in the linear
flow. It is consulted from inside Policy Engine Stage 2b for
`subscription_failure` and `b2b_receivable` events, checking for a pause condition
before any action is selected, and re-injecting broken-promise events one ladder
step higher (FR-19–FR-21, `00_CONTRACTS_RevFlow.md` §4.4).

**Cross-cutting: the B2B Ladder** (`ladder/`) is likewise consulted from Stage 3
rather than sitting in the flow, because ladder step assignment is part of action
selection, not a separate phase (FR-16).

**Cross-cutting: `contracts/`.** Not a component in the behavioural sense — it
contains no logic — but it is imported by every component and is the mechanism by
which enums, constants, and the decline map exist in exactly one place. Every
other component reads from it and none defines its own copy.

**The ordering of steps 4 and 5 is the most important line in the diagram.** The
ledger is written before the executor runs, so a crash between them leaves a
recorded decision with an unresolved outcome rather than an executed action with
no record (FR-27).

---

## 3. Component deep-dive

### 3.1 Event Ingestion (`ingestion/`)

Accepts two sources and produces one shape. `normaliser.py` maps a Razorpay
webhook payload and a synthetic dataset record onto the same internal Event
structure; `batch_loader.py` reads the generated JSON and inserts rows.

Validation happens here, before insert. A record that fails schema validation is
rejected with a logged reason and counted, never coerced into a valid-looking row
(FR-1). The distinction matters because a silently coerced row becomes an audit
entry that misrepresents its own input.

Ingestion opens a `batch_runs` row and stamps every event with its `run_id`
(FR-32). Nothing downstream queries events without a run scope.

**Does not:** classify, decide, or contact anything.

### 3.2 Root Cause Classifier (`classifier/`)

`rules.py` performs a dictionary lookup from `decline_code` to `cause` using the
map in `00_CONTRACTS_RevFlow.md` §8.2. Most events resolve here at zero cost.
`llm_fallback.py` handles the remainder — events whose code is absent, or present
but unmapped.

Two constraints on this component are easy to violate accidentally.

**Applicability is enforced.** A `cause` may only be assigned to an event whose
`event_type` appears in that cause's applies-to column
(`00_CONTRACTS_RevFlow.md` §2.2). A cause assigned outside its applicability is
rejected and replaced with `unclassified`, which routes to Stage 4. Without this
check an LLM will occasionally assign `mandate_expired` to a checkout event, and
the resulting row is nonsense that no downstream rule catches.

**`true_cause` is unreadable here.** The classifier must not query it, join to it,
or receive it in a prompt. It exists in the `events` table for the FR-4 evaluation
path only, and `metrics/classifier_eval.py` is the sole consumer. A classifier
with access to the answer key produces a precision figure that measures nothing.

**Does not:** choose actions. Cause and action are separate concerns, and merging
them is what removes the deterministic path in §3.3.

### 3.3 Policy Engine (`policy/`) — the architectural core

Four ordered stages, specified in `00_CONTRACTS_RevFlow.md` §4.2, implemented as
`hard_stops.py`, `guards.py`, `action_table.py`, and the LLM branch inside
`engine.py`.

```text
Stage 1   hard_stops.py     STOP_IF_CAUSE_IN            pure, no I/O
Stage 2   guards.py         2a retry ceiling            pure + DB reads
                            2b PTP pause / broken
                            2c cooldown
                            2d contact-frequency cap
Stage 3   action_table.py   21-row decision table       pure, table lookup
Stage 4   engine.py         bounded LLM selection       network
```

Each stage short-circuits. An event caught at Stage 1 never reaches Stage 2, and —
critically — never causes an LLM client to be constructed. This is what makes
`llm_calls_used = 0` assertable on a hard-stopped event, and `TEST-1` asserts
exactly that.

**Why Stage 3 exists.** In the v1 architecture, everything that survived the hard
stops went to the LLM for action selection. That contradicted two other documents:
`01_PRD_RevFlow.md` §9 reports the deterministic-versus-LLM split as a success
metric, and `03_Roadmap_RevFlow.md` §3 states that the ceiling means most events
never reach the LLM at all. Neither claim can be true without a deterministic path
to an action. Stage 3 supplies it via the table in
`00_CONTRACTS_RevFlow.md` §4.3, and on the specified dataset roughly 88% of events
are decided with no LLM call. This also happens to be what makes the
`LLM_CALL_BUDGET_PER_RUN` of 90 sufficient for a 300-event run, which is how the
zero-cost constraint and the boundedness claim turn out to be the same design
decision viewed from two directions.

**Stage 4 and the direction of failure.** Stage 4 is reached when
`cause = 'unclassified'` or when no §4.3 row matches. The prompt presents the
remaining allowed actions as a closed list, and the response is validated **in
code** against that list before it is trusted. Invalid, unparseable, timed out,
over budget — all four produce `action = escalate_to_human` with
`rule_fired = llm_output_rejected_defaulted`. The system fails toward a human
queue, never toward an action. `TEST-3` asserts this by feeding the validator
responses the prompt forbids.

The engine emits a decision tuple — `(action, ladder_step, rationale, rule_fired,
cause_source, llm_calls_used)` — and hands it to the ledger. It does not execute
anything.

**Does not:** perform actions, write to any table except through the ledger, or
read `true_cause`.

### 3.4 Audit Ledger (`db/ledger.py`)

One function, `insert_audit_row()`, and it is the only path by which an
`audit_log` row is created anywhere in the system. No other module holds a cursor
that writes to that table.

The single-write-path constraint is what makes NFR-1 enforceable rather than
aspirational. With one entry point, "every decision is recorded" is a property of
one function that can be tested; with writes scattered across the executor and the
ladder and the PTP tracker, it becomes a property of the whole codebase that can
only be asserted by inspection and decays with the next change.

Rows are appended and never updated or deleted (FR-26). Outcome resolution from
the executor is recorded by appending, not by mutating the earlier row.

### 3.5 Action Executor (`executor/`)

Three files, and the split between them is a safety boundary rather than an
organisational one.

`retry.py` is the only module in RevFlow that touches a payment rail. It calls
`adapters/razorpay_client.py` and records `recovered`, `failed`, or `api_error`.
It returns `api_error` rather than raising when the API is unreachable, so a
network problem degrades the run instead of ending it (FR-15).

`simulated_comms.py` generates outreach copy in the appropriate locale and writes
it to `simulated_actions`. **It imports no HTTP client, no SDK, and no socket
library.** There is nothing to disable, because there is nothing there (FR-24). The
Hinglish voice script under FR-22 and the local TTS artefact under FR-23 are
produced here, offline.

`escalation.py` writes to `escalations`. Its terminus is `flag_for_human` and
there is no state beyond it — no legal path, no collections referral, no credit
reporting (FR-17).

Every row this component writes carries its real-or-simulated status, and the API
propagates it, and the UI renders it as a tag (FR-28). A simulated action is never
presentable as a completed one at any layer.

### 3.6 API and Dashboard (`api/`, `metrics/`, `frontend/`)

`metrics/summary.py` computes the `summary_metrics.json` payload from ledger rows
and asserts the ten invariants in `00_CONTRACTS_RevFlow.md` §5.6 before returning.
`metrics/classifier_eval.py` computes FR-4 precision and recall and is the only
consumer of `true_cause`.

`api/routes.py` exposes ten endpoints, specified in
`00_CONTRACTS_RevFlow.md` §7. This document does not restate their shapes.

The frontend is a **pure read layer**. Its only non-GET call is the
`POST /run-batch` trigger, which is a run control rather than a data mutation. No
screen offers retry, override, edit, or approve. `00_CONTRACTS_RevFlow.md` §7.11
lists the endpoints that deliberately do not exist, all of which would be
decision mutations.

**No arithmetic lives in the frontend.** Every displayed figure arrives computed
(NFR-7). The frontend formats — `en-IN` grouping, paise to rupees — and nothing
else. `format.ts` is the only place a number is transformed, and it transforms
presentation, not value.

---

## 4. Data architecture

### 4.1 Tables

Seven tables. Full column lists, types, constraints, indices, and foreign keys are
in `00_CONTRACTS_RevFlow.md` §3 — that is the authority, and this table is
orientation only.

| Table | Role | Written by |
|---|---|---|
| `batch_runs` | Run scope; parent of everything | `ingestion/` |
| `events` | The recoverable items | `ingestion/` |
| `audit_log` | One row per decision, append-only | `db/ledger.py` only |
| `simulated_actions` | Outreach copy, never transmitted | `executor/simulated_comms.py` |
| `escalations` | Human review queue | `executor/escalation.py` |
| `contact_log` | Contact history backing the FR-11 cap | `executor/simulated_comms.py` |
| `ptp_commitments` | Promises to pay | `ptp/tracker.py` |

The "written by" column is a constraint, not a description. A table written from
more than one component loses the property that makes its invariants testable.

### 4.2 Entity relationships

```text
batch_runs (1) ──< events (N)
                      │
                      ├──< audit_log (N)            one per decision
                      ├──< simulated_actions (N)
                      ├──< escalations (0..N)
                      └──< ptp_commitments (0..N)

customers are not a table in Phase 0 — customer_id is a string on events.
contact_log is keyed by (customer_id, contact_date) and is deliberately
NOT scoped to a run: the FR-11 cap counts contacts to a person, and a
person does not stop being contacted because a new batch started.
```

The `contact_log` scoping note is a real design decision worth surfacing. Scoping
it per run would make the frequency cap resettable by triggering a new batch,
which is precisely the failure mode `02_Teardown_RevFlow.md` §3 attributes to
tools that count retries per campaign rather than per customer.

### 4.3 Data lifecycle — append-only and run-scoped

Each run inserts a new `batch_runs` row and scopes its events to that `run_id`.
**Nothing is truncated.** Prior runs remain queryable, and `GET /runs` lists them
(FR-32).

The v1 architecture specified that a run "truncates and repopulates `events`,
appends fresh rows to `audit_log`". That combination is a data integrity bug rather
than a style choice: truncating `events` while retaining `audit_log` orphans every
foreign key from the prior run, so the ledger becomes unreadable exactly one run
later — and the ledger is the product. `00_CONTRACTS_RevFlow.md` §3.9 replaces it
with the run-scoped model, and `08_Audit_Report_RevFlow.md` records the finding.

A full reset is available for development (`make reset` drops and recreates the
database), which is what NFR-8's "from a wiped database" refers to. That is an
explicit operator action, not something a run does implicitly.

---

## 5. API contracts

Ten endpoints. Request shapes, response shapes, status codes, and error bodies are
specified once, in `00_CONTRACTS_RevFlow.md` §7. **This document deliberately does
not restate them.** The v1 architecture listed five endpoints with inline shapes
while the SRS referenced others, and the two drifted; a single definition removes
the possibility.

What this document does own is the architectural properties of two of them.

**`POST /run-batch` is asynchronous** (FR-35). It returns 202 immediately and
executes in a background task, because a 300-event run with LLM calls exceeds any
reasonable request timeout. A second call while a run is active returns 409 rather
than queuing, since two concurrent runs writing to `contact_log` would race on the
FR-11 cap.

**`GET /events/{event_id}` omits `true_cause`.** Not filtered in the frontend —
omitted from the response model, in `contracts/schemas.py`. The withheld label must
not be reachable from the client at all, or the temptation to render
"correct/incorrect" per row leaks the answer key into the surface being evaluated.

---

## 6. Key sequence: a failed subscription payment

The path a single `subscription_failure` event takes, with the branch points named.
This is the sequence to trace when reasoning about whether a change is safe.

```text
 1. Webhook or batch loader receives the failed charge
 2. ingestion/normaliser.py       → validate → insert events row (run_id stamped)
 3. classifier/rules.py           → decline_code lookup
                                     ├── mapped   → cause, cause_source='rule'
                                     └── unmapped → classifier/llm_fallback.py
                                                     → cause, cause_source='llm'
 4. policy/engine.py Stage 1      → cause == 'user_revoked'?
                                     └── YES → action='stop', outcome='withheld',
                                               rule_fired='hard_stop_cause_in_denylist',
                                               llm_calls_used=0   ──► go to 8
 5. policy/engine.py Stage 2      → 2a retry_count >= MAX_RETRIES?  → escalate
                                     2b ptp/tracker.py: active promise? → paused
                                     2c inside COOLDOWN_HOURS?        → retry_later
                                     2d contact cap hit today?        → retry_later
 6. policy/engine.py Stage 3      → action_table.py lookup on (event_type, cause)
                                     ├── row 12/13 bank_timeout, technical_decline
                                     │             → action='retry_now'
                                     ├── row 14    insufficient_funds
                                     │             → action='retry_later'
                                     ├── row 15    mandate_expired
                                     │             → action='nudge'   (never retry)
                                     └── no match  → Stage 4
 7. policy/engine.py Stage 4      → bounded LLM, validated against closed list
                                     └── invalid/timeout → escalate_to_human,
                                         rule_fired='llm_output_rejected_defaulted'
 8. db/ledger.py                  → insert_audit_row()      ◄── BEFORE execution
 9. executor/                     → retry.py    → Razorpay Test Mode  (REAL)
                                     simulated_comms.py → DB write     (SIMULATED)
                                     escalation.py      → queue
10. outcome appended; metrics/summary.py recomputes on next /metrics read
```

Step 4 short-circuiting to step 8 with `llm_calls_used = 0` is the behaviour
`TEST-1` asserts, and step 8 preceding step 9 is the behaviour FR-27 requires.

---

## 7. Technology decisions (ADR-style)

### 7.1 Modular monolith over microservices

**Context.** Six logical components, one builder, ten days, zero budget.

**Decision.** A single FastAPI application with strict internal package
boundaries, rather than separately deployed services.

**Considered.** Microservices per component; a serverless function per stage.

**Why.** Both alternatives spend the scarce resource — days — on infrastructure
that buys nothing a judge can see. Service boundaries would add network calls
between the classifier and the policy engine, which is exactly the boundary where
in-process determinism is the point. The properties microservices would buy
(independent scaling, independent deployment, fault isolation) are all irrelevant
at 300 events on one machine.

**Consequence.** The boundaries have to be enforced by discipline rather than by
the network. The mitigation is that they are enforced by *convention plus test*:
`contracts/` is the only shared module, `db/ledger.py` is the only audit writer,
and `simulated_comms.py` contains no HTTP client. Those three constraints are what
make the monolith decomposable later — which is the substance of NFR-9, not a
vague promise about clean code.

### 7.2 SQLite over managed Postgres

**Context.** Seven tables, 300 events per run, single-writer batch access, zero
budget.

**Decision.** SQLite, file-backed, at `DATABASE_PATH`.

**Considered.** Free-tier managed Postgres (Supabase, Neon, Railway).

**Why.** The workload has no concurrency requirement — `POST /run-batch` returns
409 rather than permitting a second concurrent run, precisely so single-writer
holds. Free-tier Postgres adds a network dependency, a cold-start latency, and an
account that can expire mid-buildathon. SQLite adds a file. It is also what makes
"clone the repo and run it" true for a judge, with no provisioning step.

**Consequence.** No concurrent writers, and a migration is required for Phase 1.
The migration is bounded because the schema uses no SQLite-specific types: money
is INTEGER, timestamps are ISO-8601 TEXT, and there are no expression indices. The
schema in `00_CONTRACTS_RevFlow.md` §3 is Postgres-compatible as written apart from
the `AUTOINCREMENT` keyword.

### 7.3 Rules-first-then-LLM over pure LLM

**Context.** Both cause classification and action selection could be done entirely
by an LLM given a good prompt.

**Decision.** Deterministic paths first in both cases. `decline_code` → `cause` by
dictionary lookup; `(event_type, cause)` → `action` by decision table. The LLM
handles only what the tables cannot.

**Considered.** A single LLM call per event returning cause, action, and rationale
together.

**Why.** Three reasons, in increasing order of importance.

Cost: 300 events × one call each exceeds a free tier; roughly 36 calls does not.
Latency: a table lookup is microseconds against a second or more per call, and
NFR-6 sets a 5-second budget per decision.

And the reason that actually decides it: **a prompt is not a guarantee.** A pure-LLM
architecture can only claim boundedness by asserting that the model was instructed
well. A rules-first architecture with code-side validation can *demonstrate* it,
because the hard stop returns before the model is constructed and
`llm_calls_used = 0` is a stored fact rather than a claim. NFR-2 asks for
boundedness enforced in code, and this is the only structure that delivers it.

**Consequence.** Two places encode domain knowledge — the decline map and the
action table — and both must be maintained. `00_CONTRACTS_RevFlow.md` §8.2 and §4.3
are those two places, and the constraint that keeps them honest is that neither may
contain a value invented from memory: synthetic decline codes carry a `SYN_` prefix
so that a fabricated real code is immediately visible as a contract violation.

### 7.4 Contracts as a code package, not documentation

**Context.** Enums, constants, and the decline map are referenced by six
components and one frontend.

**Decision.** `backend/revflow/contracts/` is a real Python package generated from
`00_CONTRACTS_RevFlow.md` §2, §4.1, and §8.2, mirrored as
`frontend/lib/contracts.ts`, with a test asserting the two agree.

**Why.** The failure this prevents is the one that motivated the whole rewrite of
this document set: the same value defined in several places, drifting. A component
that imports `MAX_RETRIES` cannot disagree with the engine about what it is. A
frontend filter built from a TypeScript union that is tested against the Python
enum cannot silently go blank when a value is renamed.

**Consequence.** Adding an enum value is a documented change in two files plus a
passing test, not a one-line edit. That friction is the feature.

---

## 8. Error handling

The system's error posture is that every failure mode resolves to a *recorded*
state, never to silence and never to an unbounded action.

**External API failure (Razorpay or LLM).** Wrapped in the adapter, retried with
backoff to `LLM_MAX_ATTEMPTS`, then surfaced as a typed failure the caller must
handle. Razorpay failures record `outcome = api_error` on the audit row — a
distinct outcome, not a retry loop and not a discarded attempt (FR-15). The run
continues.

**Unreachable or unknown external endpoint.** The adapter returns `api_error`
rather than constructing a URL from memory. `00_CONTRACTS_RevFlow.md` §8.3 states
this as a hard rule: a guessed endpoint path produces a plausible-looking failure
that costs hours to diagnose, and an honest `api_error` costs none.

**Invalid LLM output.** Unparseable, empty, out-of-enum, timed out, or over
budget — all five collapse to `escalate_to_human` with
`rule_fired = llm_output_rejected_defaulted`. The system fails toward a human
queue. `TEST-3` asserts each case.

**LLM budget exhausted mid-run.** When `llm_calls_used` for the run reaches
`LLM_CALL_BUDGET_PER_RUN`, Stage 4 stops calling and every subsequent event
needing Stage 4 receives `escalate_to_human` with the same `rule_fired`. The run
completes rather than aborting, and the count of budget-defaulted events is
visible in the metrics — a degraded run that says so is more useful than a failed
one.

**Batch interrupted.** Because audit rows precede execution (§3.4), a resumed run
can be diffed against existing `audit_log` rows for that `run_id` to avoid
double-processing. This is the concrete payoff of the FR-27 ordering.

**Validation failure at ingestion.** Rejected, logged with a reason, counted, and
reported in the run summary. Never coerced (FR-1).

---

## 9. Deployment architecture

**Phase 0 (buildathon).** Backend runs locally under Uvicorn, or on a free tier if
a hosted URL is convenient. Frontend runs locally alongside it, or on Vercel's free
tier. There is no requirement for a permanently hosted URL — the deliverable is a
reproducible repository plus a recorded demo, and `make dev` starting both
processes is the supported path (NFR-8).

**Phase 1 target.** Backend containerised, deployed to a managed platform, SQLite
migrated to Postgres (§7.2), and webhook ingestion replacing the batch loader
(§4.3). **No change to the Policy Engine, Action Executor, or Audit Ledger
boundaries.** That invariance is what NFR-9 asserts, and it is a consequence of the
§7.1 discipline rather than a hope.

Secrets are read only from the environment (`00_CONTRACTS_RevFlow.md` §10.1).
`.env` is gitignored before it exists, and `git log --all --full-history --
"**/.env"` returning nothing is a submission checklist item, because a secret
removed in a later commit is still a leaked secret (NFR-4).

---

## 10. What this architecture deliberately does not solve

Named as boundaries so that encountering one is not mistaken for finding a gap.

**Multi-merchant isolation and authentication.** No tenancy model, no login, no
roles. Phase 1.

**Real outbound communication infrastructure.** Architecturally absent, not
unused — §3.5 and `00_CONTRACTS_RevFlow.md` §8.4. There is no provider to
configure and no flag to flip.

**Per-merchant policy tuning.** The ceiling config is global by design
(`04_SRS_RevFlow.md` §3.1.1, `00_CONTRACTS_RevFlow.md` §4.1). Phase 3. The five
hard stops stay non-tunable in every phase — `03_Roadmap_RevFlow.md` Appendix A
commits to this, because a system that can learn its own limits does not have
limits.

**Horizontal scale.** One machine, one writer, 300 events. Nothing here is
designed for throughput, and pretending otherwise would be the kind of claim the
rest of this document set exists to prevent.

**Streaming or scheduled operation.** Batch on trigger. No scheduler, no queue
worker, no long-lived consumer.

---

## 11. Traceability to the SRS

Every component maps to the requirements it realises. Requirement text lives in
`04_SRS_RevFlow.md`; this table is the reverse index.

| Architecture section | SRS requirements |
|---|---|
| §3.1 Event Ingestion | FR-1, FR-8, FR-9, FR-32 |
| §3.2 Root Cause Classifier | FR-2, FR-3, FR-4, FR-12 |
| §3.3 Policy Engine | FR-5, FR-6, FR-7, FR-11, FR-13, FR-14, FR-34, NFR-2, NFR-6 |
| §3.3 Stage 2b (via `ptp/`) | FR-18, FR-19, FR-20, FR-21 |
| §3.3 Stage 3 (via `ladder/`) | FR-16, FR-17 |
| §3.4 Audit Ledger | FR-26, FR-27, NFR-1, NFR-3 |
| §3.5 Action Executor | FR-10, FR-15, FR-22, FR-23, FR-24, FR-28, FR-33, NFR-4, NFR-5 |
| §3.6 API + Dashboard | FR-29, FR-30, FR-31, FR-35, FR-36, NFR-7 |
| §4 Data architecture | FR-26, FR-32, NFR-1 |
| §5 API contracts | FR-4, FR-35, and `00_CONTRACTS_RevFlow.md` §7 throughout |
| §7.4 Contracts package | FR-5, NFR-2 |
| §8 Error handling | FR-1, FR-15, NFR-2 |
| §9 Deployment | NFR-4, NFR-8, NFR-9 |
| §10 Deliberate exclusions | `04_SRS_RevFlow.md` §9 |

FR-25 has no architectural realisation in Phase 0 and is correctly absent from
this table — it is deferred (`04_SRS_RevFlow.md` §3.6).

---

**Cross-references used:** `00_CONTRACTS_RevFlow.md` §1.1, §2.2, §3, §3.9, §4.1,
§4.2, §4.3, §4.4, §5.6, §7, §7.11, §8.2, §8.3, §8.4, §9, §10.1;
`01_PRD_RevFlow.md` §9; `02_Teardown_RevFlow.md` §3;
`03_Roadmap_RevFlow.md` §3, Appendix A; `04_SRS_RevFlow.md` §3.1.1, §3.6, §5, §7,
§9, FR-1–FR-36, NFR-1–NFR-9; `06_UIUX_RevFlow.md`;
`07_Development_Plan_RevFlow.md`; `08_Audit_Report_RevFlow.md`. All resolve.
