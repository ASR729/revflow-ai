# 10 — Master Execution Prompt for Claude Code

**Document:** `10_MASTER_PROMPT_RevFlow.md`
**Purpose:** The single prompt to paste into Claude Code as your first message.

---

> **How to use this file.** Everything between the two rulers below is the prompt.
> Copy it whole and paste it as your first message in a Claude Code session opened in
> the `revflow/` folder, after completing Steps 1–13 of `09_BUILD_GUIDE_RevFlow.md`.
>
> Do not trim it, do not paraphrase it, and do not paste it in pieces. Its structure —
> comprehension gate, clarification gate, then phases separated by approval — is what
> produces phase-by-phase execution. Every section removed is a gate removed.
>
> After pasting, your only job is to read each phase report and reply `PROCEED`, or
> describe what is wrong.

---
---

# RevFlow — Build Mandate

You are implementing **RevFlow**, an agent that recovers failed Indian payments across
three pipelines (`checkout_dropoff`, `subscription_failure`, `b2b_receivable`) through
a detect → diagnose → decide → act → audit loop. It is an entry for the Razorpay AI
Buildathon, Track 03 — AI Revenue Recovery.

A complete, internally consistent specification already exists in `docs/`. Your task
is to implement it exactly. It is not to design, improve, simplify, or infer.

Read this entire prompt before doing anything.

---

## 1. Authoritative sources and precedence

Nine documents in `docs/`. No other document exists. If any of them references a
filename not on this list, that reference is a defect — report it, do not invent the
file.

| Precedence | File | Owns |
|---|---|---|
| **1 (binding)** | `00_CONTRACTS_RevFlow.md` | Enums, schemas, constants, formulas, API shapes, config, repository layout |
| 2 | `04_SRS_RevFlow.md` | Requirement identity — FR-1…FR-36, NFR-1…NFR-9 |
| 3 | `05_System_Architecture_RevFlow.md` | Components, data flow, technology decisions |
| 4 | `06_UIUX_RevFlow.md` | Design tokens, screens, components, states |
| 5 | `07_Development_Plan_RevFlow.md` | Task identity, sequencing, Definition of Done |
| 6 | `01_PRD_RevFlow.md`, `02_Teardown_RevFlow.md`, `03_Roadmap_RevFlow.md` | Intent, framing, milestones |
| — | `08_Audit_Report_RevFlow.md` | Record of defects in an earlier draft. **Not a build input.** |

**`00_CONTRACTS_RevFlow.md` wins every conflict.** If another document disagrees with
it on any technical value, doc 00 is correct and the other document is defective —
report the discrepancy, follow doc 00, and do not edit either file.

Values are defined once and quoted everywhere. If a value appears in two places and
disagrees, that is a defect to report, not a judgement call for you to make.

---

## 2. Absolute rules

These are `00_CONTRACTS_RevFlow.md` §0.4 plus the operating rules that enforce them.
They are not defaults. They do not yield to convenience, to a deadline, or to a test
that would otherwise fail.

1. **Never invent an enum value.** Every `cause`, `action`, `outcome`, `rule_fired`,
   and `ladder_step` value comes from §2. If a case arises that no value covers, use
   the designated fallback — `unclassified` for cause, `escalate_to_human` for action
   — and log it. Do not add a value.
2. **Never invent a database column.** The seven schemas in §3 are complete. A field
   you need that does not exist is a specification gap: stop and surface it.
3. **Never invent an external API endpoint path.** Especially Razorpay URLs. Implement
   only against endpoints you have verified in official Razorpay documentation. If an
   endpoint cannot be verified, the adapter returns outcome `api_error` with a clear
   message (§8.3). A plausible URL constructed from memory is the worst possible
   outcome here, because it fails in a way that looks like a network problem.
4. **Never invent a metric.** Every number the dashboard displays is computed by a
   formula in §5 from rows that exist in the database. No hardcoded values, no
   placeholder numbers shipped as real.
5. **Wireframe numbers are illustrative, not targets.** Every rupee figure and
   percentage in `06_UIUX_RevFlow.md` is layout filler. Do not hardcode them. Do not
   treat them as acceptance thresholds. The 69.4% headline and the 81% subscription
   bar are *unreachable by a correct implementation* — if your dashboard shows them,
   you have hardcoded something.
6. **Test mode only.** `RAZORPAY_KEY_ID` must match `^rzp_test_`. Assert at startup and
   refuse to boot otherwise. No override flag, no environment escape hatch.
7. **No messaging provider.** No SMS, WhatsApp, voice, or email client library in
   `requirements.txt`, `package.json`, or anywhere in the source tree. Prohibited:
   `twilio, plivo, exotel, gupshup, msg91, karix, sendgrid, mailgun, ses, boto3,
   whatsapp, smtplib`. Not stubbed, not flagged off — **absent** (§8.4).
8. **`docs/` is read-only.** If you believe a document is wrong, report the file and
   section as a defect and stop. Never edit a specification to match your code.
9. **Never commit `.env`.** NFR-4 requires that it never enter git history. No secret
   is ever logged, not even truncated.
10. **No raw card data field in any schema.**
11. **Never write a literal that doc 00 owns.** Not `3`, not `24`, not `42`, not a
    cause string, not an action string — anywhere outside `backend/revflow/contracts/`.
    Import it. A literal is a copy, and copies drift.
12. **Real NPCI and Razorpay decline codes are never written from memory.** Synthetic
    codes carry the `SYN_` prefix per §8.2.

---

## 3. The halt protocol — the most important instruction here

**If the specification does not tell you something you need, stop and ask me.**

Do not choose a sensible default. Do not infer from context. Do not implement a
simpler version that satisfies the test you had in mind. Do not proceed intending to
revisit it later.

When you halt: add a `BLOCKED` entry to `PROGRESS.md` giving the file you were
working on, the exact contract section you consulted, and the precise question. Then
stop and tell me.

Halting is not failure and it is not slow. Every hallucination in a specification-driven
build is an agent filling a gap it should have reported. Eleven halts and eleven
questions finish sooner than zero halts, because none of the eleven becomes a defect
discovered on day nine with the build on top of it.

**Halt immediately if any of these is true:**

- A value you need is not in doc 00.
- Two documents disagree and doc 00 does not settle it.
- You cannot verify an external API endpoint from official documentation.
- Implementing something as specified appears impossible.
- You are about to write a value you did not read in this session.
- A test would only pass if you changed what the requirement says.
- You are about to create a file whose path is not in §9.

---

## 4. How you will work

### 4.1 Sequential phases, one at a time

You will decompose this build into sequential phases, then execute them **strictly in
order**. Section 5 gives the phase plan; you will validate it against the dependency
graph in `07_Development_Plan_RevFlow.md` §4 during Phase 0 and tell me if you
disagree with it.

Within a phase: plan → implement → self-verify → fix → re-verify → report → **stop**.

You do not begin the next phase until I reply `PROCEED`. Not when the phase looks
finished, not when the tests pass — when I say so.

### 4.2 Ground yourself before each phase

At the start of every phase, before writing any code:

1. Re-read the contract sections that phase implements against, **in this session**.
   Not a summary, not a memory, not a persisted note from an earlier session. The file.
2. State which sections and line ranges you read.
3. Quote the specific enums, constants, schemas, and formulas the phase will use.

This costs you tokens and it is not optional. It is the difference between
implementing the contract and implementing your recollection of it. If any memory
tool offers you a remembered value, treat it as a hint about *where you are*, never as
a source for *what is true*.

### 4.3 Self-verification is by evidence

At the end of every phase you verify your own work and report **commands and their
actual output**. Never report a conclusion you have not evidenced. "Tests pass" is not
evidence. A pytest summary line is evidence.

If verification fails: fix it, then **re-run the entire verification from the top**. A
report built on a run that predates your fix is not a report.

If you cannot fix it: `BLOCKED`, and stop.

**Never mark a phase complete on a partial pass.** Nine of ten checks green is an
incomplete phase, not a complete one with a note.

### 4.4 Stay inside the phase

Do not touch files outside the current phase's declared scope. If you notice a defect
in earlier work, record it in `PROGRESS.md` and raise it in the phase report — do not
silently repair it. A fix that arrives without a report is a change I cannot review,
and it is how a build acquires modifications nobody remembers making.

Do not build anything not specified. `04_SRS_RevFlow.md` §9 and
`07_Development_Plan_RevFlow.md` §1.2 list what is deliberately out of scope. The four
most likely to be built by accident: responsive or mobile layouts, any per-event write
from the UI, any messaging provider, and runtime-editable policy config.

### 4.5 Keep `PROGRESS.md` current

Update it at every phase boundary. It is what lets a fresh session — after compaction,
after you close the terminal, after a day off — resume without re-deriving state.

```markdown
# RevFlow — Build Progress

## Status
Current phase: <n> — <name>
Last verified: <ISO date>

## Phases
| Phase | Status | Verified by | Date |
|---|---|---|---|

## Blocked
| # | Phase | File | Contract section consulted | Question | Raised |
|---|---|---|---|---|---|

## Decisions
| Date | Decision | Rationale | Approved by |
|---|---|---|---|

## Defects found in earlier phases
| # | Phase | Description | Status |
|---|---|---|---|
```

---

## 5. The phase plan

Eleven phases. Task IDs and sequencing are from `07_Development_Plan_RevFlow.md` §3
and §4; milestones from `00_CONTRACTS_RevFlow.md` §11.2. Validate this against §4's
dependency graph in Phase 0 and tell me if you disagree before we start.

### Phase 0 — Comprehension and clarification. **No code.**

Read, in this order (`00` §0.2): `00_CONTRACTS_RevFlow.md` completely, then
`04_SRS_RevFlow.md`, `05_System_Architecture_RevFlow.md`,
`07_Development_Plan_RevFlow.md`, `06_UIUX_RevFlow.md`, then `01_PRD_RevFlow.md`,
`02_Teardown_RevFlow.md`, `03_Roadmap_RevFlow.md`. Skip `08` — it is a defect record,
not a build input.

Then produce, in one message:

**(a) A comprehension report** proving you read rather than skimmed:
- The three pipelines, and which recovery actions are available to each.
- The four policy stages in order, and precisely why Stage 1 must execute before any
  LLM client is constructed.
- All sixteen constants from §4.1 with their values.
- A count of the members of each of the eleven enums in §2.
- The seven tables, and which is not run-scoped and why.
- The single write path to `audit_log`, and whether audit rows are written before or
  after the action executes.
- What `addressable_inr` counts, and why `b2b_receivable`'s recovery rate is `null`
  rather than `0`.
- Which four tests are the guardrails, and what each asserts.

**(b) Your phase plan** — the eleven phases below, each with the task IDs it contains,
the contract sections it implements against, and its exit gate. Flag any place you
think the ordering contradicts §4's dependency graph.

**(c) Every question you have.** Ask them all now, in one batch. Anything ambiguous,
anything two documents seem to disagree on, anything you would otherwise have to
choose. This is the cheapest moment in the project to ask — a question here costs a
sentence, the same question unasked costs a phase.

If you have no questions, say so explicitly and state what you would have needed to
see in order to have one. An agent with zero questions about a 5,400-line
specification has usually not read it.

Then **stop** and wait for my answers and my `PROCEED`.

### Phase 1 — Foundation and the contracts package

Tasks SET-1 … SET-4. Contract sections §9, §10.1, §2, §4.1.

Folder tree exactly per §9. Python venv, FastAPI, uvicorn, httpx, python-dotenv.
`main.py` with CORS and the startup assertions. `.env.example` with every key from
§10.1 present and blank.

**Then write `backend/revflow/contracts/`** — `enums.py` (§2), `config.py` (§4.1),
`decline_map.py` (§8.2), `schemas.py` (§7). This is a **transcription**, not a design
exercise: every enum a `StrEnum` with exactly the specified members, every constant
with exactly the specified value, nothing added, nothing renamed, nothing
"improved". After writing each file, re-read the contract section and diff it member
by member.

This ordering is the single most effective anti-drift measure in the project. Every
later task imports its values rather than choosing them. A build that reaches Phase 5
before these exist will have invented values, and invented values are invisible on
review because they look exactly like real ones.

**Gate:** `/health` returns 200. `contracts/` transcribes §2 and §4.1 with no
additions — verified by the `contract-verifier` subagent, member by member.
`RAZORPAY_KEY_ID` prefix assertion present and tested.

### Phase 2 — Database

Tasks DB-1 … DB-5. Contract sections §3, §3.9.

All seven tables per §3 — `batch_runs`, `events`, `audit_log`, `simulated_actions`,
`escalations`, `contact_log`, `ptp_commitments`. Money columns INTEGER (paise).
Append-only and run-scoped per §3.9; nothing is truncated by a run.

`contact_log` is keyed by `(customer_id, contact_date)` and is **not run-scoped** — the
FR-11 contact cap counts contacts to a person, and scoping it per run would let a new
batch reset the cap. `ptp_commitments.ladder_step_at_pause` must exist; the resume
behaviour in Phase 6 depends on it.

`insert_audit_row()` in `db/ledger.py` is the **only** write path to `audit_log`.

**Gate:** all seven tables round-trip. `git grep` proves no second writer to
`audit_log`. FKs enforced.

### Phase 3 — Adapters and the seeded dataset

Tasks INT-1, INT-2, BE-1. Contract sections §8.1, §8.2, §8.3, §6.

Razorpay adapter with `assert_test_mode()` at import and no override. LLM adapter,
provider-agnostic, with timeout, retry and budget handled inside the adapter.
**Both return typed failures and never raise** — an unreachable dependency degrades
the run, it does not end it (FR-15).

Then `scripts/generate_dataset.py` per §6: 300 events matching every distribution,
including exactly 19 hard-stop causes and 36 ambiguous events. Byte-identical across
two runs under `RANDOM_SEED`.

The 36 ambiguous events carry `decline_code` values with no mapping, which forces a
real LLM path in Phase 4 so that classifier precision is a genuine measurement rather
than a tautology. Do not give them mappable codes to make the classifier look better.

**Gate:** two consecutive generations byte-identical. One successful real Test Mode
call. One successful LLM call. Unreachable API yields `api_error`, never an exception.

### Phase 4 — Root cause classifier

Tasks BE-2, BE-3, BE-4. Contract sections §2.2, §8.1, §8.2, §5.7.

Rules first (`decline_map` lookup), LLM fallback second, applicability enforced per
§2.2. Every ambiguous event receives a valid in-enum cause; output outside
applicability is replaced with `unclassified`.

BE-4 computes precision and recall against `true_cause` and writes
`classifier_metrics.json` per §5.7. **The classifier must have no read path to
`true_cause`** — prove this by grep, not by intention. A classifier that can see the
answer is measuring nothing.

**Gate:** `classifier_metrics.json` produced from a real run. No read path to
`true_cause` anywhere in `classifier/`. Every cause in the output is in §2.2.

### Phase 5 — The policy engine. **The critical phase.**

Tasks BE-5, BE-6, and tests TEST-1, TEST-2, TEST-3. Contract sections §4.2, §4.3,
§4.4, §4.1.

`07_Development_Plan_RevFlow.md` §4 names BE-5 the single highest-risk node in the
project. Not because it is hard — it is five rules in plain Python — but because
everything that makes this product credible hangs off it. Build it carefully and do
not rush it because it looks small.

**Stage 1 — hard stops.** Plain Python, no I/O, `STOP_IF_CAUSE_IN` per §4.1. These
execute **before any LLM client is constructed**, so that `llm_calls_used = 0` on a
withheld event is a stored fact rather than a claim. This is the product's entire
differentiating argument. Trace your import and construction order and prove it —
a comment asserting the ordering is not the ordering.

**Stage 2 — guards** (DB reads): retry ceiling, PTP pause, cooldown, contact cap. Each
short-circuits.

**Stage 3 — the deterministic action table**, all 21 rows of §4.3, first-match-wins,
in the specified order. Count them when you are done. This stage is why roughly 88% of
events are decided with no LLM call, and it is why `LLM_CALL_BUDGET_PER_RUN = 90`
suffices for a 300-event batch.

**Stage 4 — bounded LLM.** Output validated **in code** against the closed action list.
Invalid, empty, malformed, or timed-out → `escalate_to_human`. Budget exhaustion
degrades; it does not abort.

**Gate:** TEST-1 — a `user_revoked` event yields `stop` with `llm_calls_used = 0`.
TEST-2 — `retry_count >= MAX_RETRIES` yields `escalate_to_human`. TEST-3 — all five
LLM failure modes yield `escalate_to_human`. All 21 rows present and ordered.
`contract-verifier` audit mandatory before you report this phase.

If TEST-1 does not pass, FR-6 is unevidenced and no amount of other completed work
compensates.

### Phase 6 — Executor, PTP tracker, B2B ladder

Tasks BE-7 … BE-11, tests TEST-4, TEST-10, TEST-11. Sections §8.3, §8.4, §4.4, §2.4.

`executor/retry.py` is the **only** module in the codebase that touches a payment rail.
`executor/simulated_comms.py` contains **no HTTP client of any kind** — not an unused
import, not a disabled one. Writes rows to `simulated_actions` and `contact_log`.
`executor/escalation.py` writes `escalations`; `flag_for_human` is terminal with no
state beyond it.

PTP tracker: detect a promise, pause until `promised_date + PTP_GRACE_DAYS`, and on a
broken promise resume **one step above** `ladder_step_at_pause` — never at
`gentle_reminder`. Ladder: step assignment from invoice age, advancing by exactly one
step per decision, never skipping.

**Gate:** TEST-4, TEST-10, TEST-11 pass. All three ladder steps appear in one run. A
PTP pause and a broken-promise escalation both appear in one run's audit log.

### Phase 7 — Orchestration, metrics, and the API

Tasks BE-12, BE-13, tests TEST-5, TEST-9. Sections §5, §5.6, §5.7, §7, §3.9.

`scripts/run_batch.py` plus `POST /run-batch` — 300 events complete unattended from a
clean database, 202 returned immediately, 409 on a concurrent call.

Metrics per §5, with **all ten invariants of §5.6 asserted in code**. `addressable_inr`
counts only `retry_now`. `recovery_rate_realised` is always paired with
`addressable_coverage`. `b2b_receivable`'s rate is explicit `null`, never `0` — a `0`
claims a failed attempt where no attempt was possible.

All ten endpoints of §7. **None is a stub.** And per §7.11, the endpoints listed there
as deliberately absent must not exist — do not add a convenience write endpoint.

**Gate:** TEST-5 — 300 events end-to-end unattended from a fresh DB, all ten invariants
hold. TEST-9 — two seeded runs structurally identical. Ten endpoints respond, none
stubbed. `contract-verifier` audit mandatory.

### Phase 8 — Frontend

Tasks FE-1 … FE-7, tests TEST-7, TEST-12. Sections §10.2, §10.3, and `06_UIUX` §2–§4.

Scaffold, then **design tokens, then the typed API client, then screens** — in that
order. FE-2 before any screen: a screen built against hand-written fetch calls and
string-literal filter values acquires its own private copy of the enums, and that copy
drifts silently.

`lib/contracts.ts` mirrors §2 and must equal `enums.py` — TEST-12 asserts it. No hex
literal in any component; tokens only. No component performs arithmetic on a metric.
`Intl.NumberFormat('en-IN')` for lakh/crore grouping, in `lib/format.ts` only.
`StatCard` and `PipelineBar` accept `number | null`. **`true_cause` appears nowhere in
the frontend.**

Every displayed number comes from `/metrics` unchanged. If a number on your screen
resembles a figure from `06_UIUX_RevFlow.md`, you have hardcoded it.

**Gate:** TEST-7, TEST-12 pass. Every figure traceable to an audit row. B2B bar renders
`—` not `0%`. Coverage displayed beside every rate.

### Phase 9 — Hardening

Tasks BE-14, INT-3, INT-4, FE-8, FE-9, BUG-1 … BUG-4, TEST-8, TEST-13, DEP-1 … DEP-3.

Offline mode (`use_llm: false`) completing a full run with no LLM call — this is what
protects the live demo from a free-tier rate limit. Hinglish script generator and a
**local** TTS sample; no cloud speech service. Loading, error and empty states, with
error copy offering no retry affordance. Accessibility pass.

BUG-4 is P0 and manual: cross-check **every** dashboard figure against `audit_log` by
hand for one full run, tracing each to the rows that produced it. A passing invariant
assertion does not prove a formula is the right formula.

**Gate:** every P0 test green. Two clean runs structurally identical. `guard_check.sh`
passes. `git log --all --full-history -- "**/.env"` returns nothing.

### Phase 10 — Submission

Tasks DEP-5, DEP-6. Work `00_CONTRACTS_RevFlow.md` §12 line by line.

README stating plainly what is real and what is simulated — retries are real Test Mode
calls, all outreach is simulated and never sent. That is a pitch asset, not a
disclaimer: volunteering the boundary is more persuasive than being asked about it.

**Gate:** §12 checklist complete. A clean checkout runs from the README alone.

---

## 6. Phase report format

At the end of every phase, output exactly this and then stop.

```
## Phase <n> — <name> — report

Contract sections re-read this session: <files and line ranges>

### Verification
| Check | Command | Result | Evidence (actual output) |
|---|---|---|---|

### Definition of done, per task
| Task ID | DoD quoted from 07 §3 | Met? | Evidence |
|---|---|---|---|

### contract-verifier verdict
<verbatim, including every finding>

### Assumptions I made
<list, or "none" — and "none" must be true>

### Values I could not find in doc 00
<list, or "none">

### Files created or modified
<list>

### Defects noticed in earlier phases
<list, or "none" — recorded, not silently fixed>

### Blocked
<list, or "none">

Phase <n> status: COMPLETE | INCOMPLETE
Awaiting PROCEED.
```

---

## 7. Forbidden behaviours

Doing any of these means the phase failed regardless of what else passed.

- Writing a value you did not read in this session.
- Substituting a simpler implementation for one you found difficult, instead of halting.
- Marking a phase complete with any check failing.
- Reporting verification you did not run, or output you did not observe.
- Editing anything in `docs/`.
- Creating a file whose path is not in §9.
- Adding a dependency from the prohibited list in §8.4.
- Hardcoding any number that should be computed.
- Building anything listed as out of scope in `04_SRS_RevFlow.md` §9.
- Continuing past a phase gate without my `PROCEED`.
- Treating a wireframe figure as a target.
- Silently repairing an earlier phase.

---

## 8. Begin

Do **not** write any code yet.

Execute **Phase 0** only: read the eight build-input documents in the order given in
§0.2, then produce the comprehension report, the phase plan, and every question you
have — all in one message.

Then stop and wait.

---
---

> **End of prompt.** Everything above the second ruler is what you paste.
