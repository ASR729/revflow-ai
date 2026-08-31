# RevFlow — Document Set Audit Report

**Document:** `08_Audit_Report_RevFlow.md`
**Version:** 1.0
**Status:** Historical record. Not binding on implementation.
**Subject:** The seven-document RevFlow v1 set, audited for interconnection integrity
**Project:** RevFlow — AI-Powered Revenue Recovery Orchestration

---

## 1. Verdict

**The v1 document set was not adequately interconnected.** An implementing agent
working from it would have been forced to invent specifications on at least twenty
occasions, and several of those inventions would have produced code that contradicts
another document in the same set.

The set was strong on intent and weak on closure. Each document was individually
coherent and well argued; the failures were almost entirely at the seams. Three
categories of defect, and one finding that was worse than a defect:

| Class | Defect | Count | Consequence if unfixed |
|---|---|---|---|
| **A** | Citations to documents that do not exist | 31 citations, 4 phantom files | Agent stalls, or invents the missing content |
| **B** | Section cross-references that resolve to the wrong section | 17 | Agent reads the wrong requirement and implements it |
| **C** | Specification gaps — a value or contract required by one document and defined nowhere | 30 | Agent invents enums, schemas, endpoints, and formulas |
| **D** | Displayed metrics the specified architecture cannot produce | 1 | The dashboard can only be built by hardcoding, which another requirement forbids |

**Total: 79 findings.** Class D is a single finding and the most important one in the
report; §6 treats it separately.

The set has been rewritten as nine documents. The additions are
`00_CONTRACTS_RevFlow.md`, a binding technical layer that closes every Class C gap,
and this report.

---

## 2. What was audited, and how

The seven input documents were the PRD, Teardown, SRS, System Architecture, Product
Roadmap, Development Plan, and UI/UX specification. Each was read in full, then read
again looking only at outbound references.

The test applied throughout was not "is this document good?" — all seven were
competent — but: **could an implementing agent proceed from here without guessing?**
Every place the answer was no became a finding, on the reasoning that an agent
which must guess will guess plausibly, and a plausible wrong guess is harder to
detect than an obvious one.

Three specific probes:

**Reference resolution.** Every filename and section number cited anywhere was
checked against what actually exists. A citation that points somewhere wrong is
worse than no citation, because it carries false confidence.

**Value closure.** For every enum, constant, column, endpoint, and formula
*referenced* by any document, is it *defined* by some document? This probe produced
the largest class.

**Cross-document contradiction.** Where two documents describe the same thing, do
they agree? This probe produced the smallest count and the most serious findings.

---

## 3. Class A — citations to documents that do not exist

Four filenames were cited across the set. None was among the seven documents
provided.

| Phantom file | Cited by | Citations | What was being cited |
|---|---|---|---|
| `01_PRD_RevFlow.md` (v1) | PRD v2.0 header | 1 | The PRD claimed to supersede an earlier PRD that was not supplied |
| `08_PRD_Professional_RevFlow.md` | Roadmap | 6 | Feature definitions and scope |
| `03_Roadmap_RevFlow.md` (as a separate file) | Roadmap, Dev Plan | 9 | Phase 1 / 2 / 3 content |
| `REVFLOW_BUILD_PROMPT` | Roadmap, Dev Plan | 15 | Build instructions and judging criteria |

The `03_Roadmap_RevFlow.md` case is the strangest: the roadmap document cited
`03_Roadmap_RevFlow.md` as though it were a *different* document containing the
phased plan, while itself being the roadmap. Either two roadmap documents existed
and one was lost, or a filename was reused. Either way an agent following the
citation lands on the document it is already reading and finds no phased plan in it.

The `REVFLOW_BUILD_PROMPT` citations were the most damaging, because several
attached load-bearing claims to it — including the buildathon judging criteria,
which the development plan used to justify its cut-order priorities. An agent cannot
verify a priority decision whose stated basis is unavailable.

### 3.1 Resolution

Per the instruction to strip rather than reconstruct: **every citation to a phantom
file was removed or redirected**, and no phantom content was invented.

The redirection was made possible by a filename decision. The nine-document set
reuses `01` through `07`, so citations of the form `01_PRD_RevFlow.md` and
`03_Roadmap_RevFlow.md` now resolve to real documents in the set. Where the cited
*content* was Phase 1/2/3 material, it is now a short, clearly labelled,
explicitly non-binding appendix inside `03_Roadmap_RevFlow.md` (Appendix A) — so a
reader following an old Phase 2 reference finds something, and that something is
marked as direction rather than specification.

The `REVFLOW_BUILD_PROMPT` citations were deleted outright. Claims that rested on
them were either re-grounded in a real document or dropped. The judging-criteria
justification in the development plan is now stated as a plain engineering argument
— a working engine with an ugly screen demonstrates more than three screens with
fabricated numbers — which stands on its own without an unavailable citation.

**Accepted loss:** whatever the original Phase 1/2/3 detail and build prompt
contained is gone. This was the explicit trade-off chosen over reconstruction, and
it is the right one: invented roadmap content would read exactly like real roadmap
content, which is precisely the failure mode this audit exists to prevent.

---

## 4. Class B — cross-references that resolve to the wrong section

Seventeen citations pointed at a real document but the wrong place in it. These are
more dangerous than Class A, because an agent following them finds *something*,
reads it as authoritative, and proceeds confidently.

| # | Citation | Points at | Should have pointed at |
|---|---|---|---|
| B1 | SRS §8 traceability → "PRD §4.1–4.7" | PRD §4 is **Non-Goals**; §4.7 does not exist | PRD §5, the Core Features section |
| B2 | UI/UX §3 → "SRS §2.1" for the no-auth scope | SRS §2.1 is Product Perspective | SRS §2.3 User Classes and §9 |
| B3 | SA §6 → "SRS Section 9, Stage J Step 30" | No such construct exists anywhere in the set | SRS §6.1 data flow |
| B4 | Dev plan §5 → "SRS §9" for judging criteria | SRS §9 is the out-of-scope list | Nothing — the claim was unsupported |
| B5 | Dev plan SET-3 → "SA §3 module boundaries" | SA §3 describes components in prose; no folder tree exists | `00_CONTRACTS` §9, the concrete tree |
| B6 | Dev plan DB-1, DB-2 → "SRS §6.2" for schemas | SRS §6.2 defined 2 of the 7 required tables | `00_CONTRACTS` §3, all seven |
| B7 | Dev plan DEP-2 → "SRS §3.7" for real-vs-simulated | SRS §3.7 is Audit Ledger and Dashboard | SRS FR-24, FR-28 |
| B8 | INT exit criteria → "SA §3.2's provider-agnostic decision" | SA §3.2 is the Root Cause Classifier | SA §7.3 and the adapter contracts |
| B9 | Dev plan TEST-1 → "SRS NFR-2" **and** "SRS §9" | The second citation is wrong | NFR-2, FR-6, FR-13 |
| B10 | Dev plan TEST-2 → "SRS FR-5" | FR-5 is the closed action enum | **FR-14**, the retry ceiling |
| B11 | UI/UX §4.2 → "§2.5" for the ledger signature | §2.5 is Motion | §2.2 Typography, the mono rule |
| B12 | UI/UX §4.2 → "§6.3" for rationale expansion | §6 had no numbered subsections | §6, the component table |
| B13 | Teardown → two PRD section numbers | Neither resolved to the described content | PRD §5, §9 |
| B14 | SA §11 traceability matrix | Omitted §3.1 and §3.2 entirely | All components must appear |
| B15 | Dev plan FE-3 → "UI/UX §4.1 module bars" | The metric is keyed by pipeline, not module | "Recovery by Pipeline" |
| B16 | Roadmap → PRD feature sections | Pointed into the phantom `08_PRD_Professional` | PRD §5 |
| B17 | UI/UX §8 → "SRS §2.5" for no-config scope | SRS §2.5 is Design Constraints — close but not the scope statement | SRS §9 |

B10 is a good illustration of why this class matters. A developer implementing
TEST-2 from the v1 plan would read FR-5, find it is about the closed action enum,
and write a test asserting that actions come from the enum — a test that already
exists as part of TEST-3. The retry ceiling, which is what TEST-2 is named for,
would go untested, and every document would still claim it was covered.

### 4.1 Resolution

All seventeen were corrected against real sections. Beyond fixing them, two
structural changes make recurrence detectable rather than invisible:

Every rewritten document ends with an explicit **"Cross-references used"** line
listing every outbound reference it makes. This turns reference integrity into
something checkable in one pass per document instead of requiring a full re-read.

Every rewritten document opens with a **precedence note** stating what it owns and
what it defers. B5, B6, and B8 all arose from a document being cited as the
authority on something it never claimed to define. Stating ownership explicitly
removes the ambiguity that produced them.

---

## 5. Class C — specification gaps

Thirty cases where one document required a value or contract that no document
defined. This was the largest class and the one most likely to produce working code
that is wrong.

### 5.1 Closed sets that were never closed

| # | Gap | Consequence |
|---|---|---|
| C1 | No closed `cause` enum. The SRS named some causes in prose, the SA named others, and the UI/UX wireframes used a third set. | An agent invents causes. Downstream rules silently never fire. |
| C2 | `insufficient_balance` (SRS) and `insufficient_funds` (elsewhere) used for the same thing. | Two near-identical enum members, one of which no rule matches. |
| C3 | No `rule_fired` value list, although the column was specified as required. | The column exists and is filled with free text, making TEST-1 unassertable. |
| C4 | `flag_for_human` used both as an action and as a ladder step. | Either the action enum grows an invalid member or the Exceptions filter misses rows. |
| C5 | No `outcome` enum, and no rule for which outcomes are valid for which actions. | `recovered` on a simulated nudge becomes representable. |
| C6 | No `cause_source` values, although FR-3 requires the column. | The deterministic-versus-LLM split cannot be computed. |
| C7 | No `locale`, `simulated_channel`, `ptp_status`, or `batch_run_status` values. | Four more free-text columns. |

C4 is the subtle one. In v1, `flag_for_human` appeared in a list of things the
system could do, alongside `nudge` and `stop`. But it is the terminal rung of the
B2B ladder, and the *action* it corresponds to is `escalate_to_human`. An agent that
adds `flag_for_human` to the action enum breaks the Exceptions screen filter, which
selects on `action IN ('stop','escalate_to_human')` — and the rows it drops are
precisely the most escalated B2B cases, the ones a finance lead most needs to see.

**Resolved:** `00_CONTRACTS_RevFlow.md` §2 defines eleven closed enums, with
`ladder_step` as a field separate from `action`, and an explicit note that putting a
ladder step into the action column violates FR-5.

### 5.2 Schemas and data lifecycle

| # | Gap | Consequence |
|---|---|---|
| C8 | Only 2 of 7 needed tables had schemas (`events`, `audit_log`). | Five tables invented. |
| C9 | No `batch_runs` table, although runs needed scoping. | FR-32 unimplementable. |
| C10 | No `contact_log`, although a contact-frequency cap was required. | FR-11 enforced in memory, unverifiable after the run. |
| C11 | No `ptp_commitments`, and no field recording the ladder step held at pause. | FR-21's "resume one step up" unimplementable — there is nothing to resume *from*. |
| C12 | No money representation rule. | Floats for currency. |
| C13 | **The data lifecycle truncated `events` while appending to `audit_log`.** | Every foreign key from the prior run is orphaned; the ledger becomes unreadable one run later. |

C13 was a genuine bug in the specification rather than an omission. The SA stated
that a run "truncates and repopulates `events`, appends fresh rows to `audit_log`".
Since audit rows reference events, the second run's truncation orphans the first
run's entire audit trail — and the audit trail is the product. An agent implementing
this faithfully would produce a system that demonstrates beautifully once and is
broken on the second run, which is exactly when a judge would ask to see it again.

**Resolved:** `00_CONTRACTS_RevFlow.md` §3 defines all seven tables with full column
lists, types, constraints, and foreign keys; money is integer paise throughout; and
§3.9 replaces truncation with an append-only run-scoped lifecycle keyed on a new
`run_id` per run.

### 5.3 The API contract

| # | Gap | Consequence |
|---|---|---|
| C14 | **`POST /run-batch` was absent**, although the dev plan and the UI/UX both assumed a Run Batch button. | The primary interaction had no endpoint. |
| C15 | `GET /config` absent, although the UI/UX specified a policy-ceiling panel. | Thresholds hardcoded in React. |
| C16 | `GET /classifier-metrics` absent, although FR-4 required the output. | The precision/recall figure has nowhere to be served from. |
| C17 | `GET /runs` absent. | No way to list or poll runs. |
| C18 | `GET /events/{id}` absent, although the UI/UX specified a detail drawer. | The drawer has no data source. |
| C19 | No statement of which endpoints must *not* exist. | Nothing prevents a `POST /retry/{id}` that breaks the append-only guarantee. |

C14 is the clearest example of a seam failure. Three documents referred to running a
batch — the dev plan as a task, the UI/UX as a button, the SRS as unattended
operation — and the API contract listed five endpoints, none of which started one.
Each document was reasonable; the set had a hole exactly where they met.

**Resolved:** `00_CONTRACTS_RevFlow.md` §7 specifies ten endpoints with request and
response shapes and status codes, including 202-plus-background-task and 409-on-
concurrent semantics for `POST /run-batch`. §7.11 lists five endpoints that
deliberately do not exist, so their absence is a specification rather than an
oversight.

### 5.4 The decision logic

| # | Gap | Consequence |
|---|---|---|
| C20 | **No deterministic action table.** SRS §3.1.1 sent everything not hard-stopped to the LLM. | Contradicts the PRD's deterministic-split success metric and the roadmap's zero-cost claim. |
| C21 | No `decline_code` → `cause` mapping. | An agent writes real-looking NPCI codes from memory. |
| C22 | Ladder monotonicity unspecified. | An invoice crossing 45 days jumps straight to `flag_for_human`, having never been reminded. |
| C23 | No config constants table; values appeared as prose in three documents. | Same threshold, three literals, eventual drift. |
| C24 | No LLM call budget. | The free tier is exhausted mid-run with no defined degradation. |
| C25 | No `RANDOM_SEED`. | BUG-2's "two structurally identical runs" is unassertable. |

C20 deserves elaboration because it is a true contradiction rather than a gap. The
PRD listed "% of events resolved by deterministic rules vs. LLM fallback" as a
success metric. The roadmap said the ceiling means most events never reach the LLM.
But the SRS's stopping rules, as written, only *stopped* events — everything
surviving them went to the LLM for action selection. So the deterministic share
would have been exactly the hard-stop rate, roughly 6%, while two other documents
implied a large majority. All three could not be true.

**Resolved:** `00_CONTRACTS_RevFlow.md` §4.2 defines four ordered stages, inserting
a deterministic action table as Stage 3, and §4.3 gives that table's 21 rows with
first-match-wins semantics and an explicit monotonicity rule. Roughly 88% of events
are now decided with no LLM call, which makes the PRD metric meaningful and the
zero-cost claim true at the same time. §4.1 fixes sixteen constants in one place,
including `LLM_CALL_BUDGET_PER_RUN` and `RANDOM_SEED`. §8.2 requires synthetic
decline codes to carry a `SYN_` prefix, so a fabricated real code is immediately
visible as a contract violation rather than passing as plausible.

### 5.5 Metrics and the dataset

| # | Gap | Consequence |
|---|---|---|
| C26 | "False-positive cost" displayed on the Overview with **no formula anywhere**. | The number is invented, or rendered as ₹0 permanently. |
| C27 | No recovery-rate denominator definition. | See §6 — this is the root of the Class D finding. |
| C28 | No synthetic dataset distribution spec. | FR-4's precision/recall becomes tautological if every code maps. |
| C29 | No `summary_metrics.json` shape. | Frontend and backend disagree on keys. |
| C30 | No test asserting backend and frontend enum lists agree. | A renamed value silently empties a filter dropdown. |

C28 is worth dwelling on. If the dataset is generated such that every event's
`decline_code` maps deterministically to its cause, then the classifier achieves
precision and recall of exactly 1.0 by construction, and FR-4 measures the lookup
table rather than the classifier. An agent satisfying the dataset requirement as
written would have destroyed the metric without any document noticing.

**Resolved:** `00_CONTRACTS_RevFlow.md` §6 fixes the full distribution — a 150/100/50
pipeline split, per-pipeline cause counts, exactly 19 guaranteed hard stops, and
**36 deliberately ambiguous events (12%) whose `decline_code` has no mapping**, which
forces a real LLM path so precision is a genuine measurement. §6.6 seeds starting
ladder steps one below each invoice's age ceiling so that a single run exercises all
three steps, making FR-16 demonstrable rather than merely specified. §5.5 supplies
the missing false-positive formula: events where the action was `retry_now` or
`nudge` while the withheld `true_cause` was in the stop denylist.

### 5.6 Priorities and milestones

Three reconciliation failures, listed here because they are gaps in agreement rather
than in content.

**A three-way priority conflict on promise-to-pay and the B2B ladder.** Simultaneously
"Must" in the SRS, "P1 / nice-to-have" in the PRD, "P1" in the development plan, and
implicitly mandatory in the roadmap's "all six modules working" definition. Meanwhile
the Teardown named PTP-aware B2B receivables as the whitespace no competitor
occupies — a differentiator the build was free to cut.

**FR-4 priority conflict.** P1 in the development plan, while the PRD reported the
figure it produces as a success metric.

**A milestone conflict.** M1 exits Day 1 in the development plan and Day 2 in the
roadmap, and the two documents disagreed on whether M2 included the Action Executor.

**Resolved:** `00_CONTRACTS_RevFlow.md` §11.1 states one priority per requirement in
all three vocabularies at once — MoSCoW, dev-plan P-level, and PRD tier — so a
conflict is now impossible to express. PTP, the ladder, and FR-4 are settled at P0.
§11.2 defines one milestone table, M1 exiting Day 2, with the Action Executor in M3;
`03_Roadmap_RevFlow.md` §4 and `07_Development_Plan_RevFlow.md` §5 both reproduce it
verbatim and say so.

---

## 6. Class D — the finding that mattered most

Everything above is a documentation defect. This one is different: it is a case where
the documents were internally consistent, individually plausible, and **jointly
described a system that could not be built as described.**

### 6.1 What was found

The UI/UX specification's Overview wireframe showed a headline recovery rate of
**69.4%**, with per-module bars of 62% for checkout drop-off, **81% for
subscription/mandate**, and 54% for B2B receivables. Elsewhere the same document
required (via NFR-7) that every displayed figure be computed from stored rows, with
no hardcoded values in source.

Both of those cannot hold, and the reason is in the decision logic.

Only one action in the entire system touches a payment rail: `retry_now`. `nudge` is
simulated and transmits nothing. `retry_later` defers. `escalate_to_human` queues.
`stop` withholds. So money can only be *realised* as recovered through `retry_now`.

Now trace the subscription pipeline. Its dominant failure cause is `mandate_expired`
— the authorisation has lapsed. The correct handling, which the SRS mandates in
FR-13 and the architecture encodes, is that `mandate_expired` **never produces a
retry**; it produces re-authorisation outreach, which is a simulated `nudge`. A
simulated nudge recovers ₹0 by construction.

An 81% subscription recovery rate is therefore not merely optimistic. It is
**unreachable by any correct implementation of the specification.**

And B2B is worse. There is no `retry_now` path for `b2b_receivable` anywhere in the
decision logic — B2B recovery is escalation, not retry. Its realised recovery is
structurally zero, and a 54% bar is not an aspiration but an impossibility.

### 6.2 Why this was the most serious finding

Every other defect in this report causes an agent to *stall* or to *invent
something detectable*. This one causes an agent to do something worse: **produce a
beautiful, plausible, hardcoded dashboard.**

Consider the position of an agent building the Overview screen. It has a wireframe
showing 69.4% and 81%. It has a working pipeline whose real output is a much smaller
number for checkout and zero for subscription and B2B. It has a requirement that the
numbers be real. The wireframe is the most concrete artefact available, and the
pressure to match it is enormous.

The most likely outcome is a dashboard that displays the wireframe figures, with the
justification that they are the specified design. That dashboard would violate NFR-7
silently, look excellent in a demo, and collapse the instant a judge asked which
audit rows produced the 81%. The product's entire thesis is that its numbers are
interrogable — so this specific failure would not merely lose a point, it would
invert the pitch.

The defect was invisible in the v1 set precisely because the two documents that
contradicted each other never referenced each other on this point. The UI/UX
document showed numbers. The SRS specified routing. Nothing joined them.

### 6.3 How it was resolved

The fix was not to lower the numbers — that would have been another invented figure.
It was to define metrics that can be honestly computed and that answer the question
the headline number was reaching for.

**Scoped denominators.** `00_CONTRACTS_RevFlow.md` §5.2 defines `addressable_inr` as
the value of events where the action was `retry_now` — the money the system actually
had a mechanism to recover. §5.3 defines `recovery_rate_realised` against that
denominator rather than against all at-risk value.

**Coverage always shown beside the rate.** `addressable_coverage` states what
fraction of at-risk value was addressable at all. A rate without it invites the
inference that unaddressed money was addressed and lost. FR-29 now requires the pair.

**An explicit null path.** `b2b_receivable`'s realised recovery rate is `null` by
design, and `06_UIUX_RevFlow.md` §4.1 requires it to render as `—` with a short
explanatory note, never as `0%`. Zero percent claims a failed attempt; null correctly
states that no mechanism exists and none is being claimed. The `StatCard` and
`PipelineBar` components take `number | null` specifically so the honest case is the
easy one to implement.

**Every wireframe figure relabelled.** `06_UIUX_RevFlow.md` now opens with a
prominent warning that all numbers in it are layout placeholders, that none is a
target or a fixture, and that copying one into a component violates NFR-7. Inside the
wireframes, the figures are replaced with typed placeholders — `‹amount›`, `‹pct›`,
`‹n›` — so there is no plausible number available to copy.

**The metric label corrected.** "Recovery by Module" became "Recovery by Pipeline",
since the metric is keyed by `event_type`. The old label invited a JSON shape keyed
by product feature that no endpoint returns.

### 6.4 The same reasoning applied to my own drafting

Worth recording, because it validates the approach. While drafting the
`summary_metrics.json` example for `00_CONTRACTS_RevFlow.md` §5.6, I wrote
illustrative figures that did not reconcile — the action breakdown summed to 310
rather than 300, and the amount partitions exceeded the stated at-risk total by about
₹5.1 lakh against ₹4.6 lakh. I caught it, discarded the draft, and rewrote §5.6 and
§5.7 using **typed placeholders plus ten asserted invariants** instead of example
values.

That change improved the document beyond fixing my arithmetic. A plausible example
payload is the single most likely thing for an implementing agent to commit as a test
fixture, and a fixture with numbers that do not reconcile teaches the codebase a
false model of its own data. Placeholders cannot be committed by accident; invariants
fail loudly. The Class D finding and my own error had the same shape, which is some
evidence that the shape is a common one.

---

## 7. What the rewrite changed structurally

Fixing 79 findings individually would have left the set as fragile as it was — the
defects were symptoms of a missing layer, not independent mistakes.

### 7.1 The contracts layer

`00_CONTRACTS_RevFlow.md` is new and is the substance of the fix. It holds every
value that more than one document needs: eleven closed enums, seven table schemas,
sixteen configuration constants, the four-stage decision pipeline, the 21-row action
table, every metric formula, the complete synthetic dataset distribution, ten
endpoint contracts, both external adapter contracts, the repository tree, environment
variables, and the reconciliation tables for priorities and milestones.

The organising rule is that **a value is defined exactly once and quoted everywhere
else.** Class C existed because values were defined zero times; the milestone and
priority conflicts existed because they were defined three times.

### 7.2 Precedence, stated

Every document now opens by declaring what it owns and what it defers, and
`00_CONTRACTS_RevFlow.md` §0.3 gives the resolution order. Ownership is:

| Document | Owns |
|---|---|
| `00_CONTRACTS` | Every technical value. Wins all conflicts. |
| `01_PRD` | Product intent, user stories, success metrics |
| `02_Teardown` | Market evidence |
| `03_Roadmap` | Scope boundaries |
| `04_SRS` | Requirement *identity* — what FR-*/NFR-* mean |
| `05_System_Architecture` | Component boundaries and data flow |
| `06_UIUX` | Tokens, layout, copy, interaction |
| `07_Development_Plan` | Task identity and sequencing |

Splitting requirement identity from technical values is what stops the SRS from
drifting against itself: requirements change slowly, values change often, and a
document owning both will disagree with an earlier version of itself.

### 7.3 Anti-hallucination provisions

Seven rules in `00_CONTRACTS_RevFlow.md` §0.4, plus specific mechanisms:

Never invent an enum value, a database column, an external endpoint path, or a
metric. Wireframe numbers are illustrative, never targets. `RAZORPAY_KEY_ID` must
match `^rzp_test_`. No messaging provider anywhere.

The mechanisms that make these enforceable rather than aspirational: synthetic
decline codes carry a mandatory `SYN_` prefix so a fabricated real NPCI code is
visible on sight; an adapter that does not know an endpoint returns `api_error`
rather than constructing a plausible URL; a named list of prohibited packages is
checked by a P0 grep (TEST-13); a test asserts the Python enums equal the TypeScript
unions (TEST-12); metric payloads use typed placeholders rather than example values;
and each document ends with a "Cross-references used" line making reference
integrity checkable in one pass.

### 7.4 Requirements and tests added

The v1 set specified behaviours it never made assertable. Six new requirements —
FR-32 through FR-36 plus the elevation of FR-33 — close the gaps that made FR-11,
FR-21, FR-32, and FR-35 unimplementable. Five new tests — TEST-9 determinism,
TEST-10 ladder monotonicity, TEST-11 PTP pause and escalated resume, TEST-12 enum
parity, TEST-13 the prohibited-package grep — cover NFR-8, FR-16, FR-21, FR-5, and
FR-24, all of which were previously specified and untested.

BUG-4, the manual cross-check of every dashboard figure against the audit log, was
promoted from P1 to P0. It is the only check that catches a metric which computes
successfully but computes the wrong thing, and given the Class D finding, that is not
a hypothetical risk.

---

## 8. What was deliberately not fixed

Recorded so that these read as decisions rather than oversights.

**The phantom documents were not reconstructed.** Their content is gone. Chosen
deliberately: invented roadmap and build-prompt content would be indistinguishable
from real content, which defeats the purpose of the audit.

**FR-25 (consent-gated live voice) remains unimplemented and is marked `Deferred`
rather than `Won't`.** It has no Phase 0 realisation and needs none, because FR-24
makes it inapplicable. Keeping it visible means the consent obligation is known from
the start rather than discovered when messaging is switched on.

**Responsive layouts moved from deferred to out of scope.** The v1 plan carried a P2
task for 375 px support. A P2 task invites someone to start it; an explicit exclusion
does not.

**Phase 1/2/3 detail is a short non-binding appendix, not a restored roadmap.** Enough
that old references resolve, clearly marked as direction.

**The Teardown's market statistics were not re-verified.** They are presented as
cited claims with their sources named, and the audit checked that the documents use
them consistently — not that the underlying figures are current. An implementing
agent does not depend on them; a pitch does, and they should be re-checked before
submission.

---

## 9. Residual risk

Honest accounting of what could still go wrong.

**The dataset distribution is asserted, not validated.** `00_CONTRACTS_RevFlow.md` §6
fixes counts that sum correctly and that I checked, but they encode assumptions about
Indian payment failure patterns drawn from the Teardown's cited figures. If those
figures are stale, the dataset is unrepresentative — which the system cannot detect
about itself. This is what Phase 1 exists to test, and
`04_SRS_RevFlow.md` §2.6 states the assumption explicitly rather than burying it.

**The ~88% deterministic share is an estimate.** It follows from the action table
covering 20 of 21 rows deterministically against the specified cause distribution.
The real figure depends on how many events land on `unclassified`, which depends on
LLM behaviour on the 36 ambiguous events. `LLM_CALL_BUDGET_PER_RUN = 90` has headroom
for roughly triple the expected Stage 4 volume, and BE-14's budget-exhaustion path
degrades honestly, so a miss is absorbed rather than fatal.

**Nine documents are more surface than seven.** The contracts layer reduces
duplication substantially, but three documents still quote the milestone table and
two quote priorities. Those quotations are labelled as quotations and I have verified
them byte-identical; a future edit to one copy would still break the set.

**The nine documents are unverified against a real build.** No code has been written
from them. The gaps this audit found were the ones visible by reading; implementation
will find others, and they will most likely be at the same seams — where a document
assumes something about a neighbour it never states.

---

## 10. Defect register

| Class | Description | Count | Status |
|---|---|---|---|
| A | Citations to non-existent documents | 31 | Stripped or redirected |
| B | Cross-references resolving to the wrong section | 17 | Corrected |
| C | Specification gaps | 30 | Closed in `00_CONTRACTS_RevFlow.md` |
| D | Displayed metrics the architecture cannot produce | 1 | Resolved via scoped denominators and an explicit null path |
| | **Total** | **79** | |

Corrective artefacts: one new binding document (`00_CONTRACTS_RevFlow.md`), seven
rewritten documents, this report, five new requirements, five new tests, one priority
promotion, and three reconciliation tables.

### 10.1 Keeping it consistent

Four checks, in increasing cost. Run the first three before any submission.

Confirm no document cites a filename outside the nine in
`00_CONTRACTS_RevFlow.md` §0.1. Confirm every FR/NFR ID cited anywhere is defined in
`04_SRS_RevFlow.md`. Confirm the milestone table is byte-identical in
`00_CONTRACTS_RevFlow.md` §11.2, `03_Roadmap_RevFlow.md` §4, and
`07_Development_Plan_RevFlow.md` §5. Then work through the pre-submission checklist
at `00_CONTRACTS_RevFlow.md` §12.

The first three are mechanical and scriptable. They were run against this set, and
§11 records the result.

---

## 11. Verification performed on the rewritten set

The rewritten nine-document set was checked programmatically, not by reading. The
checker ships with the documents as `verify_docs.py` and should be re-run after any
edit — the failure modes it catches are precisely the ones that produced the v1
defects.

| # | Check | Result |
|---|---|---|
| 1 | Every cited filename is one of the nine in §0.1 | **Pass** — 10 distinct filenames cited |
| 2 | Every cited FR/NFR is defined in the SRS; FR numbering contiguous | **Pass** — 45 cited, 45 defined, FR-1…FR-36 with no gaps |
| 3 | Every cross-document section reference resolves to a real heading | **Pass** — 423 references checked |
| 4 | Every enum header matches its listed value count; `STOP_IF_CAUSE_IN` members are declared causes | **Pass** — 57 values across 11 enums |
| 5 | No document uses an enum-shaped token that contracts §2/§3 does not declare | **Pass** |
| 6 | Every referenced constant is defined in §4.1 or §10.1 | **Pass** — 25 defined, 24 referenced |
| 7 | Every task ID in the milestone table is defined in the dev plan | **Pass** — 49 referenced, 60 defined |
| 8 | Every task ID cited anywhere is defined in the dev plan | **Pass** — 60 cited |
| 9 | Every user-story ID cited anywhere is defined in PRD §7 | **Pass** — 9 cited, 9 defined |
| 10 | Milestone table byte-identical across documents 00, 03, 07 | **Pass** — same MD5 |
| 11 | All 45 SRS priorities match contracts §11.1 exactly | **Pass** |

### 11.1 Defects the verification pass itself found

Worth recording, because it is the argument for scripting these checks rather than
trusting a careful read. Three findings surfaced on the first run of the checker
against documents I had just written and believed to be correct.

**One real defect.** `00_CONTRACTS_RevFlow.md` §11.3 and `04_SRS_RevFlow.md` §8.1 both
pointed the Audit/Dashboard row of the corrected traceability matrix at subsection
7.1 of the PRD. PRD section 7 is User Stories and has no subsections, so that
reference did not resolve — a Class B defect introduced *by the two documents that
exist to correct Class B defects*. Both now point at PRD section 7, naming US-1 and
US-8 directly.

**Two exemptions, both legitimate.** The audit report names
`08_PRD_Professional_RevFlow.md` and `REVFLOW_BUILD_PROMPT`, which do not exist —
correctly, since naming them is the finding. It also names `insufficient_balance`,
the deprecated v1 cause. The checker exempts this document specifically, and the
exemption is narrow: only document 08, only for phantom-file names.

**Two checker bugs.** The first version mis-parsed the five prose-declared enums
(§2.7–§2.11, written as ``rule`` or ``llm`` rather than as tables) and reported them
as empty. It also looked for environment variables only in §4.1 when they are defined
in §10.1. Both were checker defects, not document defects, and both were fixed —
recorded here so the pass rate is not read as having been achieved by loosening the
test.

That a freshly written correction document contained the exact class of error it was
written to fix is the most useful thing in this report. Reference integrity is not
sustainable by attention; it needs a script.

---

*The v1 documents were good documents that had not been read against each other.
That is a normal and forgivable state for a set written in sequence, and it is worth
saying plainly that the intent, the market reasoning, and the central product
insight — that restraint enforced in code is the differentiator — all survived the
audit intact and needed no defending. What the set lacked was closure: a place where
the shared values lived, and a rule about who wins when two documents disagree. Those
are now `00_CONTRACTS_RevFlow.md` and §7.2 respectively.*

---

**Cross-references used:** `00_CONTRACTS_RevFlow.md` §0.1, §0.3, §0.4, §2, §3, §3.9,
§4.1, §4.2, §4.3, §5.2, §5.3, §5.5, §5.6, §5.7, §6, §6.3, §6.6, §7, §7.11, §8.2,
§9, §11.1, §11.2, §12; `01_PRD_RevFlow.md` §5, §9; `02_Teardown_RevFlow.md` §1, §4;
`03_Roadmap_RevFlow.md` §4, Appendix A; `04_SRS_RevFlow.md` §2.3, §2.6, §6.1, §9,
FR-4, FR-5, FR-11, FR-13, FR-16, FR-21, FR-24, FR-25, FR-28, FR-29, FR-32–FR-36,
NFR-7, NFR-8; `05_System_Architecture_RevFlow.md` §7.3;
`06_UIUX_RevFlow.md` §2.2, §4.1; `07_Development_Plan_RevFlow.md` §5, §3.6, §3.7.
All resolve.
