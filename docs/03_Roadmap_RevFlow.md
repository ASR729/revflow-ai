# RevFlow — Product Roadmap (Buildathon Build)

**Document:** `03_Roadmap_RevFlow.md`
**Version:** 2.0
**Track:** 03 — AI Revenue Recovery (Razorpay AI Buildathon)
**Last updated:** 2026-08-23

**Answers:** *In what order, by when?*

**Scope:** the buildathon build (Phase 0) only. Post-buildathon direction is
summarised in **Appendix A** of this document, clearly separated and explicitly
non-binding. Appendix A exists so that references to "Phase 1" resolve somewhere
real instead of pointing at a document that was never written.

**Reads from:** `01_PRD_RevFlow.md` (features, user stories, acceptance criteria this
roadmap delivers against), `02_Teardown_RevFlow.md` (the competitive whitespace this
build is racing to prove), `00_CONTRACTS_RevFlow.md` §11.2 (the milestone table,
reproduced verbatim in §4 below).

> **Milestone authority.** `00_CONTRACTS_RevFlow.md` §11.2 is the single source of
> truth for milestones. §4 of this document and §5 of
> `07_Development_Plan_RevFlow.md` both reproduce it. If the three ever disagree,
> the contracts win and the divergence is a defect. In the v1 set these two
> documents disagreed about whether M1 landed on Day 1 or Day 2 — that is the class
> of drift this arrangement prevents.

---

## 1. Goal

Ship the core engine plus all six modules as fully working, end-to-end capabilities —
at **₹0 cost** — inside the buildathon window.

"Fully working end-to-end" means, for every module: a real event goes in, gets
classified, gets a bounded decision, gets acted on (really or honestly simulated), and
produces an auditable, dashboard-visible outcome. **Not a mocked screen. Not a
hardcoded example.** §5 below is the per-module test of that claim, and it is
deliberately stricter than "it displays something".

---

## 2. Scope — what "all six modules" means

Each module mapped to the `02_Teardown_RevFlow.md` §4 whitespace it proves. A module
that ships without its whitespace demonstrable has not shipped.

| # | Module | PRD ref | Whitespace it proves |
|---|---|---|---|
| 1 | Root Cause Classification | `01_PRD` §5.1 | India/UPI-native cause taxonomy — `02_Teardown` §4 item 2 |
| 2 | Bounded Policy Engine | `01_PRD` §5.2 | Audit and stopping rules as core architecture — `02_Teardown` §4 item 3 |
| 3 | Recovery Execution (real + simulated) | `01_PRD` §5.3 | Full-funnel coverage — `02_Teardown` §4 item 1 |
| 4 | Promise-to-Pay Tracking | `01_PRD` §5.4 | PTP married to B2B receivables — `02_Teardown` §4 item 5 |
| 5 | B2B Receivables Ladder | `01_PRD` §5.5 | Full-funnel coverage — `02_Teardown` §4 item 1 |
| 6 | Audit Ledger + Dashboard | `01_PRD` §5.6 | The differentiator against Churnkey's over-retry failure mode — `02_Teardown` §3 |

Module 3 also carries whitespace item 4 (Hinglish voice) via its script-generation
leg, delivered at M5.

**Non-goal for this roadmap:** anything listed in `01_PRD_RevFlow.md` §4. This
roadmap will not silently reintroduce a non-goal under time pressure — and because
the non-goals are enforced structurally (no messaging package installed, no legal
action in the enum), it could not do so quietly even if it tried.

---

## 3. The zero-cost constraint, made explicit

Every module is scoped so "fully working" and "₹0" are never in tension. Each
module's real-versus-simulated line is drawn so the free tier of its dependency is
never exceeded.

| Module | Dependency | ₹0 path |
|---|---|---|
| Classification | LLM fallback calls | Free-tier provider key. Rules-first design (`05_System_Architecture_RevFlow.md` §3.2) keeps call volume inside free quota; per-run budget is `LLM_CALL_BUDGET_PER_RUN` (`00_CONTRACTS` §4.1) |
| Policy Engine | LLM action selection | Same key. The deterministic ceiling plus the Stage 3 action table mean roughly seven events in eight never reach the model at all (`00_CONTRACTS` §4.2) |
| Recovery — real leg | Razorpay retries | Test Mode API. Free by design, no spend-cap risk, asserted at startup |
| Recovery — simulated leg | SMS / WhatsApp / voice | **Deliberately never integrated with any provider.** A permanent architectural choice, not a cost-saving shortcut (`01_PRD` §4) |
| Audit + Dashboard | Hosting | SQLite local file; Next.js run locally for the recording, or a free tier |
| Repo, diagrams, video | GitHub, Excalidraw, OBS | All free, no tier risk |

**Sequencing consequence.** The simulated leg has no cost ceiling, so it is safe to
build early and often. The only cost-sensitive component is LLM call volume — which
is exactly why the rules-based classifier and the deterministic ceiling are
front-loaded ahead of any LLM integration work. The cheap path and the correct
architecture happen to be the same path here, which is a convenience worth noticing
but not the reason for the design: the ordering would be right at any price.

---

## 4. Timeline

```
Week 1                                        Week 2
├─ Day 1-2 ─┬─ Day 3-4 ─┬─ Day 5 ─┬─ Day 6-7 ─┬─ Day 8-9 ──┬─ Day 10 ─┤
│ Setup +    │ Classifier│ Full    │ Dashboard │ Hardening  │ Submit   │
│ Data +     │ + Policy  │ pipeline│ (3 screens│ + voice    │          │
│ Schema     │ Engine    │ wired   │  live)    │ + PTP/B2B  │          │
│    (M1)    │   (M2)    │  (M3)   │   (M4)    │ edges (M5) │  (M6)    │
└────────────┴───────────┴─────────┴───────────┴────────────┴──────────┘
```

Reproduced verbatim from `00_CONTRACTS_RevFlow.md` §11.2:

| Milestone | Day | Contents | Exit criteria |
|---|---|---|---|
| **M1** Foundation | 2 | SET-1–4, DB-1–5 | `/health` returns 200; all seven tables round-trip; 300-event dataset generated and byte-reproducible under `RANDOM_SEED` |
| **M2** Core engine | 4 | BE-1–6, INT-1–2 | **TEST-1 passes**: a `user_revoked` event yields `stop` with `llm_calls_used = 0`. TEST-2, TEST-3 pass. |
| **M3** Full pipeline | 5 | BE-7–13 | TEST-5 passes: 300 events end-to-end unattended from a fresh DB; all ten §5.6 invariants hold |
| **M4** Dashboard | 7 | FE-1–7 | All three screens render live data; every displayed number traces to an audit row; ≥1 `stop` clickable on Exceptions |
| **M5** Hardened | 9 | INT-3–4, BE-14, FE-8–9, BUG-1–4, DEP-1–3 | All P0 tests green; two clean runs structurally identical; every module has a clickable real audit example |
| **M6** Submitted | 10 | DEP-5–6 | Repo reproducible from clean checkout; video shows all six modules |

### What each milestone actually delivers

**M1 — Foundation (Day 2).** Repo, environment, all seven database tables, synthetic
dataset generator. Ships nothing user-facing; this is the groundwork every module
depends on. The dataset's cause distribution is grounded in `02_Teardown_RevFlow.md`
§1 (the ~70% payment-linked checkout figure) rather than chosen for convenience —
see `00_CONTRACTS_RevFlow.md` §6.3.

**M2 — Core engine (Day 4).** Modules 1 and 2 fully working. A single event can be
classified and correctly decided, **including the stop case**. Its exit criterion is
the most important test in the project: a revoked-mandate event produces `stop` with
zero LLM calls. That test is the proof of the entire bounded claim in
`02_Teardown_RevFlow.md` §4 item 3. Note that the Action Executor is *not* in M2 —
it belongs to M3, which keeps M2's exit criterion clean and unambiguous.

**M3 — Full pipeline (Day 5).** Recovery Execution (both legs), PTP Tracking, and the
B2B Ladder wired into batch orchestration. The full 300-event set runs end-to-end,
unattended, producing real test-mode retry calls, honestly-labelled simulated nudges,
PTP pauses, and ladder steps — **all six modules touched by one real run, not six
disconnected demos.** Exit also requires all ten metric invariants in
`00_CONTRACTS_RevFlow.md` §5.6 to hold, which is what makes "real, non-hardcoded
numbers" checkable rather than a matter of opinion.

**M4 — Dashboard (Day 7).** Module 6 across all three screens. Overview, Audit Trail,
and Exceptions render real data from the M3 pipeline, every number traceable to an
audit row. At least one `stop` visible and clickable on Exceptions — the acceptance
story for the whole product (`01_PRD` US-3).

**M5 — Hardened (Day 9).** Hinglish voice script plus one local TTS sample, PTP and
ladder edge cases hardened, everything re-verified together. Nothing left as a stub
or a "coming soon". Exit requires every module in §2 to have at least one traceable
real audit example a judge could click during the pitch.

**M6 — Submitted (Day 10).** Documentation, demo video, repo hygiene. Reproducible
from a clean checkout at ₹0 by anyone following the README.

---

## 5. Definition of "fully working end-to-end"

Per module, the roadmap's real bar. Check against this before declaring anything done.

| Module | Not done if… | Done when… |
|---|---|---|
| Root Cause Classification | Causes are hardcoded or randomly assigned | A real decline code or an LLM call produces the cause, measurably — precision and recall reported (FR-4) |
| Bounded Policy Engine | The LLM is trusted to self-police its own boundaries | A deterministic, LLM-free check runs first and is unit-tested against the `user_revoked` case (TEST-1) |
| Recovery Execution | A "real" retry is just a database write with no API call | At least one retry is a verified live Razorpay Test Mode API response |
| PTP Tracker | Promises are stored but never actually pause anything | A paused event is demonstrably skipped until its promised date, **and** a broken promise resumes the ladder one step further on (FR-21) |
| B2B Ladder | Every invoice gets the same message regardless of age | Ladder step assignment visibly changes with invoice age in the audit log, advancing at most one step per decision (`00_CONTRACTS` §4.3) |
| Audit Ledger + Dashboard | Dashboard numbers are typed in by hand for the demo | Every number renders from a live read of the metrics endpoint, refreshable by re-running the batch — and no numeric literal exists anywhere in `frontend/` |

The PTP row gained its second clause and the ladder row its monotonicity clause
because the v1 versions were passable by an implementation that paused correctly but
forgot the pause afterwards, or one that jumped straight to `flag_for_human` on an
old invoice. Both would have looked correct in a demo.

---

## 6. Risks specific to the zero-cost constraint

| Risk | Mitigation |
|---|---|
| Free-tier LLM rate limit hit mid-batch or during the live demo | Rules-first design (§3) keeps call volume low; `LLM_CALL_BUDGET_PER_RUN` caps it hard. Pre-run and cache the batch output before recording — **never depend on live calls during the pitch.** `POST /run-batch` accepts `use_llm: false` for a fully offline demo path (`00_CONTRACTS` §7.2) |
| Free-tier hosting cold-starts or sleeps during the demo | Not required. Running locally during the recording removes this risk entirely; no hosted URL is needed for submission |
| Temptation to "just use a paid messaging API for reliability" under time pressure | The ₹0 constraint is a stated project value, not merely a budget limit. The simulated-comms boundary is architectural (`01_PRD` §4), and the prohibited-package grep is a P0 gate (`00_CONTRACTS` §8.4) — so this cannot be done quietly even at 2am on Day 9 |

The third row is the one that has teeth. A stated value under deadline pressure is a
suggestion; a failing check in the submission gate is a decision.

---

## Appendix A — Post-buildathon direction (non-binding)

**This appendix is not a commitment and nothing in the Phase 0 build depends on it.**
It exists so that the phrase "Phase 1" resolves to something concrete instead of
dangling. It is deliberately thin: a buildathon roadmap that also tries to sell a
twelve-month plan tends to undersell how tightly scoped and achievable the actual
submission is.

**Phase 1 — sandbox shadow mode.** Run against a real merchant's sandbox traffic in
observe-only mode: classify and decide, write audit rows, execute nothing. The value
is calibrating the classifier against real decline codes instead of the `SYN_`-prefixed
synthetic ones (`00_CONTRACTS` §8.2). NFR-9 exists so this is a configuration change
rather than a redesign.

**Phase 2 — supervised live pilot.** Real actions on a small cohort, with a human
approving anything the policy engine routes to `escalate_to_human`, and real messaging
integrated behind explicit per-customer consent (FR-25, currently deferred). Note the
consequence: consent capture, provider integration, and DPDP review all land here, and
none of them are small.

**Phase 3 — per-merchant tuning and live voice.** Learned thresholds per merchant
rather than the fixed constants in `00_CONTRACTS_RevFlow.md` §4.1, and live Hinglish
voice calls. **The hard stops in Stage 1 remain fixed and non-tunable in every phase.**
Making restraint learnable would remove the property that distinguishes RevFlow from
everything in `02_Teardown_RevFlow.md` §3 — an optimiser given control of its own
limits reliably discovers that fewer limits score better.

---

**Cross-references used:** `00_CONTRACTS_RevFlow.md` §4.1, §4.2, §4.3, §5.6, §6.3,
§7.2, §8.2, §8.4, §11.2; `01_PRD_RevFlow.md` §4, §5.1–5.6, US-3;
`02_Teardown_RevFlow.md` §1, §3, §4; `05_System_Architecture_RevFlow.md` §3.2;
`07_Development_Plan_RevFlow.md` §5. All resolve.
