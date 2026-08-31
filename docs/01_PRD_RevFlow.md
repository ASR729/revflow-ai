# RevFlow — Product Requirements Document

**Document:** `01_PRD_RevFlow.md`
**Version:** 3.0 (supersedes all earlier PRD drafts)
**Status:** Binding for Phase 0 (buildathon)
**Event:** Razorpay AI Buildathon — Track 03, AI Revenue Recovery
**Last updated:** 2026-08-23

> **Read `00_CONTRACTS_RevFlow.md` first.** It defines the enums, schemas, config
> constants, formulas, and API surface that this document describes in prose. Where
> this document and the contracts differ, **the contracts win**. This PRD contains
> no enum values, no schema definitions, and no numeric thresholds of its own —
> only pointers to where they are defined.

**Document set** (nine files, no others exist):

| # | File | Answers |
|---|---|---|
| 00 | `00_CONTRACTS_RevFlow.md` | What are the exact values, names, and shapes? |
| 01 | `01_PRD_RevFlow.md` | What are we building and why? *(this document)* |
| 02 | `02_Teardown_RevFlow.md` | What already exists and where is the gap? |
| 03 | `03_Roadmap_RevFlow.md` | In what order, by when? |
| 04 | `04_SRS_RevFlow.md` | What exactly must the software do? |
| 05 | `05_System_Architecture_RevFlow.md` | How is it structured? |
| 06 | `06_UIUX_RevFlow.md` | What does it look like? |
| 07 | `07_Development_Plan_RevFlow.md` | Which task, in which order, tested how? |
| 08 | `08_Audit_Report_RevFlow.md` | What was wrong with v1 and how was it fixed? |

---

## 1. One-paragraph summary

RevFlow is an agentic revenue-recovery layer for Indian businesses. When a payment
fails, a subscription mandate breaks, or a B2B invoice ages past due, RevFlow
diagnoses *why*, decides what a competent human collections operator would do, does
it within hard limits it cannot exceed, and writes down its reasoning before acting.
The product's distinguishing claim is not that it recovers more — it is that **it
knows when to stop**, and can prove it. Every decision is bounded by deterministic
policy that executes before any language model is consulted, and every decision
leaves an append-only audit row containing the rule that authorised it.

---

## 2. The problem

Indian revenue recovery fails in three distinct places, and the failures have
different causes that current tooling treats identically.

**Checkout drop-off.** Roughly 70% of Indian cart abandonment is payment-linked
rather than intent-linked — the customer wanted to buy and the payment step failed
them (`02_Teardown_RevFlow.md` §2). Generic abandoned-cart email treats a bank
timeout and a change of mind as the same event, and sends the same message to both.

**Subscription and mandate failure.** UPI Autopay mandate success sits in the
30–50% band (`02_Teardown_RevFlow.md` §2). A mandate can fail because the account
was momentarily short, because the mandate expired, or because the customer revoked
it. The first is worth retrying. The second needs re-authorisation. **The third is
a withdrawal of consent, and retrying it is a compliance problem, not an
optimisation opportunity.** Existing dunning tools retry all three.

**B2B receivables.** Invoice chasing in India is relationship-mediated. The
correct next step depends on invoice age, on whether the customer has disputed it,
and above all on whether they already promised to pay. Automated chasers that
re-send a reminder to a customer who committed to paying on the 14th do measurable
damage to the commercial relationship.

The common failure across all three is the same: **tools escalate on a timer, not
on a diagnosis, and they have no notion of a boundary they must not cross.**

---

## 3. Goals

| # | Goal | How it is evidenced |
|---|---|---|
| G-1 | Diagnose cause before choosing action | `cause` and `cause_source` on every event; classifier precision/recall computed, not asserted (FR-2, FR-4) |
| G-2 | Never exceed a stated boundary | Deterministic stops execute before any LLM call; TEST-1 proves it (NFR-2) |
| G-3 | Explain every decision | Rationale + `rule_fired` on every audit row, no exceptions (FR-7, NFR-3) |
| G-4 | Respect withdrawn consent absolutely | `user_revoked` and `invoice_disputed` terminate processing (FR-13, NFR-5) |
| G-5 | Report honestly | Every displayed number computed from the audit log; scope of each rate stated (NFR-7) |
| G-6 | Cover all three loss surfaces in one engine | One policy engine, three pipelines, shared audit ledger |

**G-2 and G-5 are the goals that matter.** A recovery tool that cannot demonstrate
its own limits is a liability, and a dashboard whose numbers cannot be traced to a
decision is a demo, not a product.

---

## 4. Non-goals

Explicitly out of scope for Phase 0. Each of these is a deliberate exclusion, not
an oversight, and the architecture is built so that none of them can be added by
accident.

| Non-goal | Why | Enforced by |
|---|---|---|
| Sending any real message — SMS, WhatsApp, email, voice call | No consent has been collected from any real person | No messaging provider is installed; the prohibited-package grep is a P0 check (`00_CONTRACTS` §8.4) |
| Storing or handling raw card data | Out of PCI scope entirely | No schema field exists for it (NFR-4) |
| Automated escalation to legal or collections | Requires human commercial judgement | `escalate_to_human` is terminal; there is no legal action in the action enum (FR-17) |
| Deciding *whether* to grant a refund or waiver | Commercial decision, not a recovery decision | Not in the action enum |
| Live production traffic | Test-mode only, asserted at startup | `RAZORPAY_KEY_ID` must match `^rzp_test_`, no override (`00_CONTRACTS` §8.3) |
| Multi-tenant isolation, RBAC, authentication | Single-operator demo | No auth layer exists; documented, not stubbed |
| Predicting future churn | RevFlow reacts to failures that already happened | No forecasting component |
| Recovering payments outside India | UPI/NPCI-specific taxonomy | `locale` enum is `en-IN`, `hi-IN`, `hinglish` only |

Two of these deserve emphasis because they are the ones a builder is most likely to
"helpfully" add:

**There is no messaging integration and adding one is a defect.** Nudges are
recorded in `simulated_actions` and labelled *SIMULATED* in every surface that
displays them. This is not a stub awaiting a provider key — the absence is the
design (FR-24, FR-28).

**Voice is a script plus one local audio file, not a call.** RevFlow generates a
Hinglish script and renders exactly one sample clip locally, to demonstrate tone
calibration. Nothing dials anything (FR-22, FR-23).

---

## 5. Core features

Six modules. The word *module* here means one of these six product capabilities —
distinct from *pipeline* (three event types) and *component* (six runtime code
packages). See `00_CONTRACTS_RevFlow.md` §1 for the vocabulary.

### 5.1 Module 1 — Cause classifier

Turns a raw failure into one of a closed set of causes. Deterministic mapping runs
first: a known decline code maps straight to a cause with no model involved. Only
genuinely ambiguous events reach the language model, and its output is validated
against the closed enum before use — an unrecognised value is rejected, not coerced.

Every classification records whether it came from the rule map or the model
(`cause_source`), which is what makes FR-4's precision and recall meaningful rather
than circular.

*Requirements:* FR-1, FR-2, FR-3, FR-4. *Enums:* `00_CONTRACTS` §2.2, §2.7.

### 5.2 Module 2 — Bounded policy engine

The core of the product. Four stages run in strict order:

1. **Hard stop.** Causes representing withdrawn consent or active dispute
   terminate immediately.
2. **Guards.** Retry ceiling, cooldown, contact cap, active promise-to-pay.
3. **Deterministic action table.** A first-match-wins table covering the ordinary
   cases — roughly seven in eight events are decided here.
4. **Bounded language model.** Only what remains. The model chooses from the same
   closed action set, under a per-run call budget, with a validation gate on the way
   out and a safe default if it fails.

**Stages 1 through 3 contain no language model call.** This is the structural
property the product is built on: boundedness is a consequence of execution order,
not of instruction-following. A prompt can be argued with; a Python `if` returning
before the network call cannot.

*Requirements:* FR-5, FR-6, FR-7, FR-34. *Stages:* `00_CONTRACTS` §4.2.
*Action table:* §4.3.

### 5.3 Module 3 — Three recovery pipelines

One engine, three entry points.

*Checkout drop-off* separates a failed payment attempt from a plain browse-and-exit
within a bounded session window, and treats them differently — a bank timeout gets
a retry, an abandonment gets at most a single nudge.

*Subscription and mandate failure* distinguishes insufficient funds (retry with
backoff), expired mandate (re-authorisation nudge, never a retry), and revoked
mandate (stop). Retries are bounded by both a ceiling and a cooldown, and each one
records the rule that authorised it.

*Hinglish voice* generates a script whose tone is calibrated to the diagnosed
cause — a bank timeout is not the customer's fault and the script does not imply it
is — and renders one sample clip locally.

*Requirements:* FR-8 through FR-15, FR-22, FR-23, FR-24, FR-33.

### 5.4 Module 4 — Promise-to-pay tracker

Reads a simulated customer reply, decides whether it contains a commitment to pay,
extracts the date, and **pauses all further contact until that date passes**. If the
promise is kept, the matter closes. If the date passes without payment, the ladder
resumes **one step further along than where it paused** — a broken promise is
information, and RevFlow does not forget it and start over.

This is the module that most directly separates RevFlow from timer-driven dunning,
and it is the reason PTP is P0 rather than a nice-to-have.

*Requirements:* FR-19, FR-20, FR-21. *Ladder resume rule:* `00_CONTRACTS` §4.3.

### 5.5 Module 5 — B2B escalation ladder

Invoice age determines how far the ladder *may* advance, not where it lands. Each
decision moves at most one step: gentle reminder, then firm reminder, then flag for
a human. The ladder never regresses, and it never advances past flagging — legal and
collections are human decisions (FR-17).

A disputed invoice exits the ladder entirely.

*Requirements:* FR-16, FR-17, FR-18. *Steps:* `00_CONTRACTS` §2.4.
*Monotonicity rule:* §4.3.

### 5.6 Module 6 — Audit ledger and dashboard

Every decision writes an append-only row **before** the action executes, containing
the event, the cause, the cause source, the action, the rule that fired, the
rationale, the outcome, and whether the action was simulated. Nothing is updated in
place. Nothing is deleted.

The dashboard is a pure read layer over that ledger. It performs no writes and
exposes no retry button — every number on it resolves to rows you can click through
to. Simulated actions are visually distinct from real ones everywhere they appear.

*Requirements:* FR-26 through FR-32, FR-35, FR-36. *Metric definitions:*
`00_CONTRACTS` §5.

---

## 6. Users

**Primary — recovery operator at an Indian D2C or SaaS business.** Runs a batch,
reads the exceptions list, acts on what was flagged. Needs to know what RevFlow
did and why, and needs to trust that it did not contact anyone it shouldn't have.
The exceptions view is built for this person: it is the *first* thing they should
open, not the last.

**Secondary — finance lead.** Cares about how much was actually recovered versus
how much was merely addressed, and will notice immediately if those two numbers are
conflated. This is why `00_CONTRACTS` §5.1 scopes every rate and displays
`addressable_coverage` alongside it.

**Tertiary — compliance reviewer.** Asks one question: show me a case where the
system chose to stop. The Exceptions screen answers it in one click.

---

## 7. User stories

| ID | Story | Priority | Requirements |
|---|---|---|---|
| US-1 | As an operator, I run one batch and see every decision it made, with reasons | P0 | FR-26, FR-29, FR-32, FR-35 |
| US-2 | As an operator, I see *why* each payment failed, not just that it did | P0 | FR-2, FR-3, FR-4 |
| US-3 | As a compliance reviewer, I can find a case where RevFlow chose not to act | P0 | FR-6, FR-13, FR-31 |
| US-4 | As an operator, I trust that a revoked mandate is never retried | P0 | FR-13, NFR-5 |
| US-5 | As an operator, retries stay within a limit I can state out loud | P0 | FR-14, FR-15, NFR-2 |
| US-6 | As a finance lead, invoice chasing escalates by age and stops before legal | P0 | FR-16, FR-17 |
| US-7 | As an operator, a customer who promised to pay is left alone until that date — and resumes one step up if the promise breaks | P0 | FR-18, FR-19, FR-20, FR-21 |
| US-8 | As an operator, I can tell at a glance which actions were simulated | P0 | FR-24, FR-28 |
| US-9 | As a finance lead, I can distinguish money recovered from money addressed | P0 | NFR-7, `00_CONTRACTS` §5.1 |

**US-3 is the acceptance story for the whole product.** If a reviewer cannot find a
deliberate stop in one click, RevFlow has not demonstrated the thing it claims.

---

## 8. Priorities

Priorities are defined once, in `00_CONTRACTS_RevFlow.md` §11.1, in all three
vocabularies (MoSCoW, development-plan P-level, PRD tier) simultaneously. **This
document does not restate them**, because restating them is exactly how the v1 set
ended up asserting three different priorities for promise-to-pay.

Two things worth stating in prose:

**Promise-to-pay and the B2B ladder are P0.** `02_Teardown_RevFlow.md` §4 names
PTP-aware B2B receivables as whitespace no competitor occupies. A differentiator
claimed in the teardown cannot be optional in the build.

**Classifier precision/recall (FR-4) is P0.** It is a success metric in §9 below.
A metric that might not be computed is not a metric.

---

## 9. Success metrics

Every metric below is computed from the audit ledger at run time. None is
configurable, hardcoded, or estimated. The formulas live in
`00_CONTRACTS_RevFlow.md` §5; this section says what each one is *for*.

**Boundedness (the hard gate).** Zero out-of-bounds actions, zero decisions
lacking a rationale, zero retries beyond the ceiling, zero contact events during
an active promise-to-pay. These are not targets to approach — **any non-zero value
is a build failure**, checked by `00_CONTRACTS` §12.

**Classification quality.** Precision and recall per cause, against the withheld
ground truth. The withheld labels are read only by the metrics component and by
nothing else, which the pre-submission grep verifies.

**Recovery, stated honestly.** Only one action in the set touches a real payment
rail. Recovery is therefore reported as: money *addressable* by a real retry,
money *realised*, the ratio between them, and — critically — the fraction of
at-risk money that was addressable at all. Reporting the ratio without the
coverage would overstate performance, so the dashboard is contractually forbidden
from showing one without the other.

For B2B receivables the addressable amount is structurally zero, because no path
through the action table sends a receivable to a real retry. Its realised recovery
rate is therefore **`null`, and renders as an em dash, not as 0%.** Rendering it as
0% would imply RevFlow tried and failed; `—` states correctly that this pipeline
was never in scope for realised recovery in Phase 0. This distinction is the
clearest single example of what NFR-7 is asking for.

**Restraint.** How many events were deliberately stopped, and the estimated cost
of the false positives avoided — computed as the events where an unbounded tool
would have retried or nudged a customer whose true cause was a revocation or a
dispute (`00_CONTRACTS` §5.5).

**Efficiency.** Share of decisions made without any language model call. Expected
to be high by construction, since stages 1 through 3 precede the model.

---

## 10. Dependencies and constraints

| Dependency | Nature | Failure behaviour |
|---|---|---|
| Razorpay API, **test mode only** | Real retries against test payments | On any error: `outcome = api_error`, decision and audit row still written |
| One LLM provider | Ambiguous classification and stage-4 decisions | Per-run call budget; on failure or invalid output, `escalate_to_human` with `rule_fired = llm_output_rejected_defaulted` |
| Local TTS | One sample audio clip | Missing binary degrades to script-only; documented, not fatal |
| SQLite | Single-file datastore | — |
| Synthetic dataset | 300 events, seeded, byte-reproducible | Regeneration under the same seed must produce identical bytes |

**Constraints.** Ten days, single builder, buildathon scope. No production traffic
at any point. No real recipient contacted at any point. No secret committed at any
point in git history — verified by a `git log --all --full-history` check, because
checking the working tree alone would miss the case that matters
(`07_Development_Plan_RevFlow.md` DEP-3).

---

## 11. Risks

| Risk | Consequence | Mitigation |
|---|---|---|
| Language model returns an action outside the set | Unbounded behaviour, product claim void | Validation gate, safe default, TEST-3 |
| Metrics quietly hardcoded to look better | NFR-7 violated, product is a demo | No numeric literal permitted in the frontend; §12 grep |
| Simulated actions read as real | Reviewer misled | Every simulated row carries `outcome = simulated` and is labelled in every surface |
| Recovery rate presented without scope | Overstates performance | `recovery_rate_realised` cannot be displayed without `addressable_coverage` |
| Six modules half-built, none demonstrable | Nothing to show | M5 exit requires a clickable real audit example per module |
| Enum drift between backend and frontend | Runtime mismatch | A test asserts the Python and TypeScript enums are identical |
| Live-mode key used by accident | Real money moved | Startup assertion on `^rzp_test_`, no override flag exists |

---

## 12. Compliance posture

RevFlow's compliance stance is not a policy document, it is the four stages of
§5.2. Consent withdrawal is a hard stop that executes before any model runs, so it
cannot be reasoned around. No real communication channel exists, so no unconsented
message can be sent even by mistake. No card data field exists in any schema, so
none can be stored. Legal escalation is absent from the action enum, so it cannot
be chosen.

Phase 0 is a test-mode demonstration on synthetic data. Nothing here constitutes
legal or regulatory advice, and a production deployment would need RBI, NPCI, and
DPDP review that is out of scope for this document.

---

## 13. Go / No-Go

Ship only if all of the following hold. These are gates, not aspirations.

- [ ] TEST-1 passes: a revoked mandate yields `stop` with zero language-model calls
- [ ] TEST-2, TEST-3, TEST-5 pass, twice, from a wiped database
- [ ] Every boundedness counter is zero
- [ ] Every number on the dashboard traces to audit rows
- [ ] No numeric literal in the frontend
- [ ] B2B realised recovery renders as `—`, not `0%`
- [ ] Exceptions screen shows at least one deliberate stop, clickable
- [ ] All six modules have a real audit example
- [ ] The prohibited-package grep returns nothing
- [ ] `git log --all --full-history -- "**/.env"` returns nothing
- [ ] README states plainly what is real and what is simulated

**If the first item fails, do not ship.** Everything else in RevFlow is a claim
about how well it recovers money. That one is the claim that it knows when not to
try — and it is the only claim the competitive landscape leaves open
(`02_Teardown_RevFlow.md` §4).
