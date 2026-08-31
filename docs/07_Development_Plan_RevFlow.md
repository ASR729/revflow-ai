# RevFlow — Development Plan

**Document:** `07_Development_Plan_RevFlow.md`
**Version:** 2.0 (rewritten for cross-document consistency)
**Status:** Binding for task identity and sequencing. Subordinate to `00_CONTRACTS_RevFlow.md` on any technical value.
**Project:** RevFlow — AI-Powered Revenue Recovery Orchestration
**Track:** Razorpay AI Buildathon, Track 03 — AI Revenue Recovery
**Window:** 10 days, one builder

---

> **Precedence.** This document owns **task identity and sequencing** — what SET-1
> through DEP-6 are, what each depends on, and in what order they get built. It
> does not own enums, schemas, constants, endpoint shapes, or milestone dates;
> those are in `00_CONTRACTS_RevFlow.md` and win on conflict. The milestone table
> in §5 is reproduced verbatim from `00_CONTRACTS_RevFlow.md` §11.2 and must not
> be edited here.
>
> Priorities are **P0 / P1 / P2** in this document. The same requirements carry
> MoSCoW levels in `04_SRS_RevFlow.md` and tiers in `01_PRD_RevFlow.md`. All three
> vocabularies are reconciled in one table at `00_CONTRACTS_RevFlow.md` §11.1 —
> consult it rather than inferring an equivalence.

---

## 1. Scope for developers

### 1.1 In scope

A batch system that ingests 300 synthetic events across three pipelines,
classifies each one's cause, decides an action within a hard ceiling, executes real
retries through Razorpay Test Mode, writes simulated outreach it never sends,
tracks promises to pay, escalates B2B receivables through a bounded ladder, and
presents everything through a read-only dashboard.

All six modules in `01_PRD_RevFlow.md` §5 ship working. `03_Roadmap_RevFlow.md` §2
defines what "working" means per module, and it is a lower bar than "polished" but a
strictly higher bar than "present in the code".

### 1.2 Explicitly out of scope — do not build, do not gold-plate

`04_SRS_RevFlow.md` §9 is the authoritative list. The four most likely to be built
by accident:

**Responsive and mobile layouts.** Desktop only (`06_UIUX_RevFlow.md` §10). The v1
plan carried a P2 task for 375 px support; it is now out of scope rather than
deferred, because a P2 task invites someone to start it.

**Any per-event write from the UI.** No retry button, no override, no approve. The
"Mark reviewed" control on the Exceptions screen is local React state and nothing
more (`06_UIUX_RevFlow.md` §4.3).

**Any messaging, telephony, or email provider.** Not stubbed, not flagged off —
absent. TEST-13 enforces this.

**Runtime-editable policy config.** `GET /config` reads. Nothing writes.

---

## 2. Priority framework

| Level | Meaning | If the schedule slips |
|---|---|---|
| **P0** | The submission is not viable without it. | Never cut. |
| **P0-critical** | P0, and on the critical path with the highest downstream risk. | Never cut; build first. |
| **P1** | Substantially weakens the demo or the pitch if missing. | Cut only after every P0 is green. |
| **P2** | Polish. | Cut freely. |

Two priority changes from v1, both traceable to
`00_CONTRACTS_RevFlow.md` §11.1.

**BE-4 (classifier precision/recall) moves P1 → P0.** It computes a figure
`01_PRD_RevFlow.md` §9 reports as a success metric. A metric that might not be
computed is not a metric.

**BE-10 and BE-11 (PTP tracker, B2B ladder) move P1 → P0.**
`02_Teardown_RevFlow.md` §4 stakes RevFlow's differentiation on PTP-aware B2B
receivables. A differentiator claimed in the teardown cannot be optional in the
build. The v1 document set asserted three different priorities for this
capability — Must in the SRS, P1 in the PRD, P1 here — which is exactly the class
of conflict `00_CONTRACTS_RevFlow.md` §11.1 now prevents.

---

## 3. Workstream breakdown

### 3.1 Setup — SET

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| SET-1 | Obtain Razorpay Test Mode keys + one LLM provider key | P0 | — | Both stored in `.env`; one successful test call made to each; `RAZORPAY_KEY_ID` matches `^rzp_test_` |
| SET-2 | Init git repo with `.gitignore` **before** any `.env` exists | P0 | — | `git status` has never shown `.env`; `git log --all --full-history -- "**/.env"` is empty |
| SET-3 | Create the folder tree | P0 | SET-2 | Matches `00_CONTRACTS_RevFlow.md` §9 exactly, path for path |
| SET-4 | Python venv + FastAPI/uvicorn/httpx/dotenv; write `contracts/` package | P0 | SET-3 | `/health` returns 200; `contracts/enums.py` and `config.py` transcribe `00_CONTRACTS_RevFlow.md` §2 and §4.1 with no additions |

**SET-2 ordering is not pedantry.** A `.gitignore` written after the first commit
is a `.gitignore` that may already have missed something, and NFR-4 requires that
`.env` never appear in history — not that it be removed later.

**SET-4 includes the contracts package**, and that is deliberate. Writing
`enums.py` and `config.py` first means every subsequent task imports its values
rather than choosing them, which is the single most effective anti-drift measure
available. A build that reaches BE-5 before the enums exist will have invented some.

*Exit criteria:* a running FastAPI app answering `/health`, keys stored and never
committed, and a `contracts/` package that is a faithful transcription of doc 00.

### 3.2 Database — DB

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| DB-1 | `batch_runs` + `events` tables | P0 | SET-4 | Insert/read round-trip passes; `run_id` FK enforced; money columns are INTEGER |
| DB-2 | `audit_log` table | P0 | DB-1 | Round-trip passes; `rule_fired` and `rationale` are NOT NULL |
| DB-3 | `simulated_actions` + `escalations` tables | P0 | DB-2 | FKs to `events` and `audit_log` verified |
| DB-4 | `contact_log` + `ptp_commitments` tables | P0 | DB-2 | `contact_log` keyed by `(customer_id, contact_date)` and **not** run-scoped; `ptp_commitments.ladder_step_at_pause` present |
| DB-5 | `insert_audit_row()` as the single write path | P0 | DB-2 | No other function anywhere writes to `audit_log`; verified by grep |

All five follow `00_CONTRACTS_RevFlow.md` §3 — seven tables, not the four the v1
plan specified. The three that were missing (`batch_runs`, `contact_log`,
`ptp_commitments`) each back a P0 requirement: FR-32, FR-33, and FR-21
respectively. A build that stops at four tables cannot satisfy any of them.

**DB-4's non-run-scoping is a real constraint, not an oversight.** The FR-11
contact cap counts contacts to a person. Scoping `contact_log` per run would let a
new batch reset the cap, which is the failure mode `02_Teardown_RevFlow.md` §3
attributes to tools that count per campaign
(`05_System_Architecture_RevFlow.md` §4.2).

*Exit criteria:* all seven tables exist, and it is structurally true — not merely
documented — that no action can be recorded without an audit row.

### 3.3 Backend core logic — BE

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| BE-1 | `generate_dataset.py` | P0 | DB-1 | 300 valid events matching every distribution in `00_CONTRACTS_RevFlow.md` §6, including exactly 19 hard-stop causes and 36 ambiguous events; byte-identical across two runs under `RANDOM_SEED` |
| BE-2 | Root Cause Classifier — rules | P0 | BE-1 | Resolves the non-ambiguous majority with zero LLM calls; applicability enforced per §2.2 |
| BE-3 | Root Cause Classifier — LLM fallback | P0 | BE-2, INT-2 | Every ambiguous event receives a valid in-enum cause; out-of-applicability output replaced with `unclassified` |
| BE-4 | Classifier evaluation vs `true_cause` | **P0** | BE-3 | `classifier_metrics.json` produced from a real run; classifier code proven to have no read path to `true_cause` |
| BE-5 | Policy Engine Stages 1–2 — hard stops + guards | **P0-critical** | BE-3 | `user_revoked` / `invoice_disputed` → `stop` with `llm_calls_used = 0`; all four guards short-circuit correctly |
| BE-6 | Policy Engine Stages 3–4 — action table + bounded LLM | **P0-critical** | BE-5 | All 21 rows of §4.3 implemented first-match-wins; LLM output validated in code against the closed list; invalid → `escalate_to_human` |
| BE-7 | Action Executor — real retry via Razorpay Test Mode | P0 | BE-6, INT-1 | One real Test Mode attempt completes end-to-end; unreachable API yields `api_error`, never an exception |
| BE-8 | Action Executor — simulated comms writer | P0 | BE-6 | No HTTP client exists in this code path at all; rows written to `simulated_actions` and `contact_log` |
| BE-9 | Action Executor — escalation queue | P0 | BE-6 | `escalations` rows written; `flag_for_human` is terminal with no state beyond it |
| BE-10 | PTP Tracker | **P0** | BE-6, DB-4 | Detects a promise, pauses to `promised_date + PTP_GRACE_DAYS`, resumes **one step above** `ladder_step_at_pause` on a broken promise |
| BE-11 | B2B escalation ladder | **P0** | BE-10 | Step assignment matches invoice-age rules; advances by exactly one step per decision; never skips |
| BE-12 | `run_batch.py` orchestration + `POST /run-batch` | **P0-critical** | BE-2 … BE-11 | 300 events complete unattended from a clean DB; 202 returned immediately; 409 on a concurrent call |
| BE-13 | Metrics computation + all ten API endpoints | P0 | BE-12 | `summary_metrics.json` from real rows with all ten §5.6 invariants asserted; ten endpoints respond; none is a stub |
| BE-14 | Offline mode (`use_llm: false`) + LLM budget guard | P1 | BE-13 | A full run completes with no network to the LLM; budget exhaustion degrades to `escalate_to_human` rather than aborting |

**BE-5 is the highest-risk node in the project.** Everything downstream depends on
it: TEST-1, the Exceptions screen, the withheld-cases metric, and the entire
boundedness pitch. It is also small — five rules in plain Python — which is exactly
why it is easy to defer and then rush. Build it before anything that consumes it.

**BE-6 splits from BE-5 on purpose.** Stage 3 (the deterministic action table) is
the piece the v1 plan had no task for at all, which is how the v1 architecture
ended up sending every non-stopped event to the LLM — contradicting both the PRD's
deterministic-split metric and the roadmap's zero-cost claim
(`05_System_Architecture_RevFlow.md` §3.3).

**BE-14 exists because of one specific demo risk.** The LLM free tier can rate-limit
during a live pitch. An offline path that produces a complete, honest run without
any LLM call means the demo never depends on a third party being available at the
wrong moment. It is P1 only because a pre-recorded run is an acceptable fallback.

*Exit criteria:* `run_batch.py` runs top to bottom with no intervention, producing a
populated `audit_log` and a real `summary_metrics.json` whose invariants all hold.

### 3.4 Frontend — FE

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| FE-1 | Scaffold Next.js app | P0 | — (parallel to backend) | Renders locally; fonts self-hosted via `next/font/google` |
| FE-2 | Typed API client + `contracts.ts` | P0 | BE-13, FE-1 | Wrappers for all ten endpoints; TS unions mirror `enums.py`; TEST-12 passes |
| FE-3 | Design tokens | P0 | FE-1 | CSS custom properties per `06_UIUX_RevFlow.md` §2; no hex literal in any component |
| FE-4 | Overview screen | P0 | FE-2, FE-3 | Numbers match `/metrics` exactly; coverage shown beside the rate; B2B bar renders `—` not `0%` |
| FE-5 | Audit Trail screen | P0 | FE-2, FE-3 | Sortable and filterable; `[REAL]`/`[SIMULATED]` tags correct; `rule_fired` visible on every row |
| FE-6 | Exceptions screen | P0 | FE-2, FE-3 | Separates `stop` from `escalate_to_human`; the two group counts sum to the endpoint total |
| FE-7 | Event Detail Drawer | P1 | FE-5 | Opens from any row; full rationale, `cause_source`, `llm_calls_used`, PTP state; **no `true_cause` anywhere** |
| FE-8 | Loading, error, and empty states | P1 | FE-4, FE-5, FE-6 | Skeletons on load; empty state before first run; error copy offers **no** retry affordance |
| FE-9 | Accessibility pass | P1 | FE-4 … FE-7 | Keyboard reachable with visible focus ring; contrast verified; `aria-label` on stat cards including the null case |

**FE-2 before any screen.** Building a screen against hand-written fetch calls and
string-literal filter values is how a frontend acquires its own private copy of the
enums. The typed client plus `contracts.ts` makes drift a test failure.

**FE-4's three conditions are each a requirement, not polish.** Coverage beside the
rate is FR-29. `—` rather than `0%` is NFR-7. Numbers matching `/metrics` exactly
means no arithmetic in the component. The v1 wireframe's 69.4% headline and 81%
subscription bar were unachievable by the specified architecture, and the only way
to display them would have been to hardcode them — see
`08_Audit_Report_RevFlow.md`.

*Exit criteria:* all three screens render live backend data and match the tokens and
layout in `06_UIUX_RevFlow.md`.

### 3.5 Integrations — INT

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| INT-1 | Razorpay Test Mode adapter | P0 | SET-1 | `assert_test_mode()` at import with no override; returns typed failure rather than raising; verified by BE-7 |
| INT-2 | LLM provider adapter | P0 | SET-1 | Provider-agnostic interface; timeout, retry, and budget handled inside the adapter; verified by BE-3 and BE-6 |
| INT-3 | Hinglish script generator | P1 | INT-2 | Produces a tone-calibrated script per cause — apologetic where the rail failed, neutral where the payer did |
| INT-4 | Local TTS sample | P1 | INT-3 | One playable audio file produced entirely offline; no cloud speech service |

**Both adapters must return typed failures, never raise.** An unreachable
dependency degrades the run; it does not end it (FR-15,
`05_System_Architecture_RevFlow.md` §8). And per
`00_CONTRACTS_RevFlow.md` §8.3, an adapter that does not know an endpoint path
returns `api_error` rather than constructing a plausible URL from memory.

*Exit criteria:* both external dependencies sit behind thin adapters, and swapping
LLM providers requires touching no file in `policy/`.

### 3.6 Testing — TEST

| ID | Task | Priority | Depends on | Maps to |
|---|---|---|---|---|
| TEST-1 | `user_revoked` / `invoice_disputed` → `stop`, `llm_calls_used = 0` | **P0-critical** | BE-5 | FR-6, FR-13, NFR-2 |
| TEST-2 | `retry_count >= MAX_RETRIES` → `escalate_to_human` | P0 | BE-5 | **FR-14** |
| TEST-3 | Invalid / empty / malformed / timed-out LLM output → `escalate_to_human` | P0 | BE-6 | NFR-2, FR-5 |
| TEST-4 | One real Razorpay Test Mode call | P0 | BE-7 | FR-15 |
| TEST-5 | Clean-state 300-event batch, unattended, invariants hold | **P0-critical** | BE-13 | NFR-8, NFR-7 |
| TEST-6 | Classifier precision/recall computed | P0 | BE-4 | FR-4 |
| TEST-7 | Frontend smoke — three screens, live data, no console errors | P1 | FE-4 … FE-6 | FR-29–31 |
| TEST-8 | Manual UAT of the judge journey | P1 | FE-7, FE-8 | `06_UIUX_RevFlow.md` §5.1 |
| TEST-9 | Two seeded runs are structurally identical | P0 | BE-12 | NFR-8 |
| TEST-10 | Ladder monotonicity — no step is skipped; all three steps appear in one run | **P0** | BE-11 | FR-16 |
| TEST-11 | PTP pause holds; broken promise resumes one step up, never at `gentle_reminder` | **P0** | BE-10 | FR-20, FR-21 |
| TEST-12 | `enums.py` values equal `contracts.ts` values | P0 | FE-2 | FR-5 |
| TEST-13 | Prohibited-package grep returns nothing outside `docs/` | P0 | BE-8 | FR-24, NFR-5 |

Five of these are new relative to v1. TEST-9, TEST-10, and TEST-11 exist because
NFR-8, FR-16, and FR-21 were otherwise unasserted — the v1 plan specified the
behaviours and tested none of them. TEST-12 and TEST-13 exist because enum drift
and an accidentally added messaging dependency are both silent failures that no
other test would catch.

**TEST-2's mapping is corrected.** The v1 plan mapped it to FR-5, which is the
closed action enum. The retry ceiling is FR-14.

> **The four guardrail tests are TEST-1, TEST-2, TEST-3, and TEST-5**
> (`00_CONTRACTS_RevFlow.md` §11.4, `04_SRS_RevFlow.md` §8.4). These four pass
> regardless of what else slips. If TEST-1 does not pass, FR-6 is unevidenced and
> no amount of other completed work compensates — the product's central claim is
> that restraint is structural, and TEST-1 is the executable form of that claim.

*Exit criteria:* the four guardrail tests pass consistently, and TEST-10, TEST-11,
TEST-12, and TEST-13 pass at least once before submission.

### 3.7 Bug fixing and hardening — BUG

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| BUG-1 | Fix all P0 test failures | P0 | TEST-1 … TEST-6, TEST-9 … TEST-13 | Every P0 test green |
| BUG-2 | Full pipeline from a wiped DB, twice, structurally identical | P0 | TEST-5, TEST-9 | Two clean unattended runs; same counts, same decisions, same `rule_fired` distribution |
| BUG-3 | Review every LLM prompt for outputs that could escape the allow-list | P0 | BE-6 | Validation confirmed to catch and default in all five failure modes |
| BUG-4 | Cross-check every dashboard figure against `audit_log` by hand for one full run | P0 | FE-4 … FE-6 | No discrepancy; each figure traced to the rows producing it |
| BUG-5 | Non-critical polish — copy, spacing, minor visual | P2 | all above | Time-permitting only |

**BUG-4 is promoted from P1 to P0.** It is the manual counterpart to NFR-7 and the
only check that catches a metric that is computed but computed wrongly. A number
that traces to no row is the specific failure this document set was rewritten to
prevent, and a passing invariant assertion does not prove a formula is the right
formula.

*Exit criteria:* zero known P0 bugs; the two guardrail behaviours — hard stop and
retry ceiling — verified twice independently.

### 3.8 Documentation and deployment — DEP

| ID | Task | Priority | Depends on | Definition of done |
|---|---|---|---|---|
| DEP-1 | `docs/architecture.md` + README with real run instructions | P0 | BE-13 | A clean checkout runs by following the README exactly, with no undocumented step |
| DEP-2 | README "what is real, what is simulated" section | P0 | BE-8 | States plainly that retries are real Test Mode calls and all outreach is simulated and never sent |
| DEP-3 | Confirm `.env` never committed, full history | P0 | — | `git log --all --full-history -- "**/.env"` returns nothing |
| DEP-4 | Optional free-tier deploy | P2 | FE-4 … FE-6, BE-13 | Public URL matches local behaviour, if attempted |
| DEP-5 | Record the demo video | P0 | all P0 above | Shows the problem, the architecture, a live batch run, one real recovery, one correctly-withheld case, and final metrics |
| DEP-6 | Final push + submission | P0 | DEP-5 | Repo and video links submitted |

**DEP-2 is a pitch asset, not a disclaimer.** Volunteering the real/simulated
boundary is more persuasive than being asked about it, and it is the same argument
as showing withheld cases on the Overview rather than behind a click.

Copy the nine documents into `docs/` per `00_CONTRACTS_RevFlow.md` §9 as part of
DEP-1. An implementing agent working from a checkout needs `00_CONTRACTS_RevFlow.md`
present, not referenced.

*Exit criteria:* the repo is clean, documented, reproducible by a stranger, and the
video is recorded and uploaded.

---

## 4. Dependency graph

```text
SET-1 ─┬─ SET-2 ─ SET-3 ─ SET-4 ─┬─ DB-1 ─ DB-2 ─┬─ DB-3
       │                          │               ├─ DB-4
       │                          │               └─ DB-5
       ├─ INT-1 ──────────────────┼──────────────────────────┐
       └─ INT-2 ──────────┐       │                          │
                          │       ▼                          │
                          │     BE-1  (dataset, seeded)      │
                          │       │                          │
                          │     BE-2  (classifier: rules)    │
                          │       │                          │
                          └────► BE-3  (classifier: LLM)     │
                                  │                          │
                                BE-4  (precision / recall)   │
                                  │                          │
                        ╔═════════▼═════════╗                 │
                        ║ BE-5  Stages 1–2  ║ ◄── highest-risk node
                        ║ hard stops+guards ║                 │
                        ╚═════════╤═════════╝                 │
                                  │  └──────────► TEST-1  ★   │
                        ╔═════════▼═════════╗                 │
                        ║ BE-6  Stages 3–4  ║                 │
                        ║ table + bounded   ║                 │
                        ╚═════════╤═════════╝                 │
                                  │  └──────────► TEST-2 ★ TEST-3 ★
              ┌───────────┬───────┼───────┬──────────┐        │
              ▼           ▼       ▼       ▼          ▼        │
            BE-7 ◄────────┴──── BE-8   BE-9      BE-10        │
          (real retry)      (simulated)(escalate) (PTP)  ◄────┘
              │                 │        │          │
              │                 │        │        BE-11 (ladder)
              │                 │        │          │
              └────────┬────────┴────────┴──────────┘
                       ▼
                    BE-12  run_batch + POST /run-batch
                       │
                    BE-13  metrics + ten endpoints
                       │  └──────────► TEST-5 ★  TEST-9
                       │
   FE-1 ─ FE-3 ─┬───► FE-2 ─┬─ FE-4 ─┐
                │            ├─ FE-5 ─┼─► FE-7 ─ FE-8 ─ FE-9
                │            └─ FE-6 ─┘
                │                  └──────────► TEST-7, TEST-8
                │
             BE-14 (offline mode)   INT-3 ─ INT-4
                       │
                       ▼
              BUG-1/2/3/4 ─► DEP-1/2/3 ─► DEP-5 ─► DEP-6

★ = guardrail test (non-negotiable)
```

**The true critical path** is Setup → Database → Classifier → **Policy Engine
(BE-5, BE-6)** → Executor → Orchestration (BE-12) → Metrics and API (BE-13) →
Frontend data screens → Testing → Hardening → Submission.

**BE-5 is the single highest-risk node.** Not because it is technically hard — it is
five rules in plain Python — but because everything that makes the demo credible
hangs off it: TEST-1, the Exceptions screen, the withheld-cases figure, and the
whole boundedness argument. Its risk profile is "small, easy to postpone, and
catastrophic to get wrong late."

**FE-1 and FE-3 parallelise with the backend.** Scaffold and tokens need no API.
FE-2 is the first frontend task that blocks on BE-13, so the ordering above puts the
unblocked work first.

---

## 5. Milestones

Reproduced verbatim from `00_CONTRACTS_RevFlow.md` §11.2. **Do not edit this table
here** — `03_Roadmap_RevFlow.md` §4 carries the same table, and the v1 set placed M1
at Day 1 here and Day 2 there. One definition, two copies, both quoted.

| Milestone | Day | Contents | Exit criteria |
|---|---|---|---|
| **M1** Foundation | 2 | SET-1–4, DB-1–5 | `/health` returns 200; all seven tables round-trip; 300-event dataset generated and byte-reproducible under `RANDOM_SEED` |
| **M2** Core engine | 4 | BE-1–6, INT-1–2 | **TEST-1 passes**: a `user_revoked` event yields `stop` with `llm_calls_used = 0`. TEST-2, TEST-3 pass. |
| **M3** Full pipeline | 5 | BE-7–13 | TEST-5 passes: 300 events end-to-end unattended from a fresh DB; all ten §5.6 invariants hold |
| **M4** Dashboard | 7 | FE-1–7 | All three screens render live data; every displayed number traces to an audit row; ≥1 `stop` clickable on Exceptions |
| **M5** Hardened | 9 | INT-3–4, BE-14, FE-8–9, BUG-1–4, DEP-1–3 | All P0 tests green; two clean runs structurally identical; every module has a clickable real audit example |
| **M6** Submitted | 10 | DEP-5–6 | Repo reproducible from clean checkout; video shows all six modules |

**If the timeline compresses, protect M1, M2, M3, TEST-1, and TEST-5 above
everything else.** Those are the difference between a working agent and a UI mockup
with fabricated numbers — and the second is the failure mode the track brief
penalises most heavily. A dashboard with three screens and no working policy engine
demonstrates nothing; a working policy engine with one ugly screen demonstrates the
entire thesis.

Note what this implies about cut order: **the frontend is cut before the engine.**
FE-7, FE-8, and FE-9 are all P1 for exactly this reason.

---

## 6. Definition of done — project level

The project is ready to submit when every one of these holds. This list is the
short form; `00_CONTRACTS_RevFlow.md` §12 is the full pre-submission checklist and
should be worked through line by line.

**Correctness**

- [ ] `run_batch.py` completes unattended from a wiped database, twice, with identical structural behaviour (BUG-2, TEST-9)
- [ ] TEST-1, TEST-2, TEST-3, TEST-5 all pass — the four guardrails
- [ ] TEST-10, TEST-11, TEST-12, TEST-13 pass
- [ ] All ten `summary_metrics.json` invariants assert true on a real run

**Demonstrability**

- [ ] At least one `stop` and one `escalate_to_human` exist and are visible on Exceptions
- [ ] All three ladder steps appear in one run's audit log
- [ ] Both a PTP pause and a broken-promise escalation appear in one run's audit log
- [ ] All six modules have a clickable real audit example
- [ ] Every dashboard figure traces on click to the audit rows that produced it

**Honesty**

- [ ] No hardcoded rupee value, count, or percentage anywhere in frontend or backend source
- [ ] `b2b_receivable` recovery rate renders as `—`, not `0%`
- [ ] `addressable_coverage` is displayed beside every recovery rate
- [ ] README states plainly what is real and what is simulated

**Safety**

- [ ] `RAZORPAY_KEY_ID` starts `rzp_test_`; the startup assertion exists and is tested
- [ ] The prohibited-package grep returns nothing outside `docs/`
- [ ] `git log --all --full-history -- "**/.env"` returns nothing
- [ ] No raw card data field exists in any schema

**Deliverables**

- [ ] A stranger can set up and run the project from a clean checkout using the README alone
- [ ] Demo video shows the problem, the architecture, a live batch run, one real recovery, one correctly-withheld case, and the final metrics

---

## 7. Risk register

| Risk | Workstream | Impact | Mitigation |
|---|---|---|---|
| LLM free-tier rate limit hit during the live demo | BE, INT | Demo fails on stage | **BE-14 offline mode** — a full run completes with `use_llm: false`. Also pre-run and cache output before recording. Never depend on a live LLM call during the pitch. |
| Policy Engine ceiling has a logic gap | BE-5, BE-6 | The worst possible failure — it invalidates the entire pitch | TEST-1/2/3 are P0-critical and re-run under BUG-2 before submission. BE-5 is built first, not last. |
| Synthetic distribution looks unrealistic to a judge | BE-1 | Judges question data validity | Distributions are derived from the cited public figures in `02_Teardown_RevFlow.md` §1 and fixed in `00_CONTRACTS_RevFlow.md` §6. Say so in the demo rather than waiting to be asked. |
| Classifier accuracy is trivially perfect | BE-1, BE-4 | FR-4 measures nothing; the metric is exposed as tautological | The 36 ambiguous events in `00_CONTRACTS_RevFlow.md` §6.3 carry `decline_code` values with no mapping, so a real LLM path is forced and precision is a genuine measurement. |
| Enum drift between backend and frontend | FE-2 | Filters silently empty; a value renders blank | TEST-12 asserts `enums.py` equals `contracts.ts`. Drift fails a test rather than surfacing in the demo. |
| A convenience dependency reintroduces a messaging client | BE-8 | FR-24 and NFR-5 silently violated | TEST-13 greps the repository. Absence is enforced, not documented. |
| Metrics compute but compute the wrong thing | BE-13, FE-4 | A number that traces to no row — the exact failure this document set exists to prevent | Ten asserted invariants in `00_CONTRACTS_RevFlow.md` §5.6, plus BUG-4 manual cross-check promoted to P0. |
| Truncate-style data lifecycle orphans the ledger | DB-1, BE-12 | The audit trail becomes unreadable one run later | Run-scoped append-only per `00_CONTRACTS_RevFlow.md` §3.9. Nothing is truncated by a run. |
| Scope creep into responsive layouts or UI writes | FE | Days spent on work that is explicitly out of scope | Both are in `04_SRS_RevFlow.md` §9 and §1.2 above as exclusions rather than deferred tasks. |
| Ten days is not ten days | all | Milestones slip | Cut order is fixed: P2, then P1, then nothing. The frontend is cut before the engine. |

---

**Cross-references used:** `00_CONTRACTS_RevFlow.md` §2, §2.2, §3, §3.9, §4.1, §4.3,
§5.6, §6, §6.3, §8.3, §9, §11.1, §11.2, §11.4, §12; `01_PRD_RevFlow.md` §5, §9;
`02_Teardown_RevFlow.md` §1, §3, §4; `03_Roadmap_RevFlow.md` §2, §4;
`04_SRS_RevFlow.md` §8.4, §9, FR-4, FR-5, FR-6, FR-11, FR-13, FR-14, FR-15, FR-16,
FR-20, FR-21, FR-24, FR-29, FR-30, FR-31, FR-32, FR-33, NFR-2, NFR-4, NFR-5, NFR-7,
NFR-8; `05_System_Architecture_RevFlow.md` §3.3, §4.2, §8;
`06_UIUX_RevFlow.md` §2, §4.3, §5.1, §10; `08_Audit_Report_RevFlow.md`. All resolve.
