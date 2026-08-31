# RevFlow — UI / UX Specification

**Document:** `06_UIUX_RevFlow.md`
**Version:** 2.0 (rewritten for cross-document consistency)
**Status:** Binding for visual design, copy, and interaction. Subordinate to `00_CONTRACTS_RevFlow.md` on any data value.
**Project:** RevFlow — AI-Powered Revenue Recovery Orchestration
**Track:** Razorpay AI Buildathon, Track 03 — AI Revenue Recovery

---

> ## ⚠ Every number in this document is a layout placeholder
>
> The figures in the wireframes below — rupee amounts, percentages, counts, event
> IDs — exist to show where text sits and how wide it runs. **None is a target,
> a fixture, or an expected result.** Every displayed value comes from
> `GET /metrics`, `GET /audit-log`, or `GET /exceptions` at runtime.
>
> NFR-7 forbids hardcoded figures in frontend source. An implementing agent that
> copies `₹2,84,600` or `69.4%` from a wireframe into a component has violated it,
> and `00_CONTRACTS_RevFlow.md` §12 includes a check for exactly this.
>
> This warning exists because the v1 version of this document showed a plausible
> 69.4% headline rate and an 81% subscription bar that **the specified
> architecture cannot produce** — `mandate_expired` routes to a simulated `nudge`,
> which recovers no money, so an 81% subscription recovery rate could only have
> come from hardcoding. See `08_Audit_Report_RevFlow.md`.

---

> **Precedence.** This document owns tokens, layout, copy, and interaction. It does
> not own metric definitions, enum values, or endpoint shapes — those are in
> `00_CONTRACTS_RevFlow.md` and win on conflict. Requirement identity is in
> `04_SRS_RevFlow.md`.

---

## 1. Design principles

**1. Honesty is the aesthetic.** The interface's job is to make a sceptical reader
believe the numbers. That means showing what was withheld as prominently as what
was recovered, labelling every simulated action, and rendering an undefined rate as
`—` rather than as a confident zero. A dashboard that looks impressive and cannot
be interrogated is worth less here than one that looks plain and can.

**2. The ledger is the metaphor.** Monospaced figures, left vertical rules on rows,
flat surfaces, right-aligned amounts. It should read like a register someone is
accountable for, not a growth dashboard.

**3. Calm register.** Amber for at-risk rather than red. Crimson reserved for
`stop` and `withheld` only, used like a stamp. No ultra-bold weights, no ambient
motion. A financial operations tool earns trust by being still.

**4. Answer the first question above the fold.** "How much did we recover, and can
I trust it?" — three stat cards, no chart clutter.

**5. One flourish, earned.** The rotated `WITHHELD` stamp on `stop` rows. It is the
only decorative element in the system, and it decorates the thing the product is
actually about.

---

## 2. Design tokens

### 2.1 Colour — six named values, light-mode base

| Token | Hex | Usage |
|---|---|---|
| `--canvas` | `#F7F8FA` | Page background. Soft neutral, not cream. |
| `--ink` | `#12161C` | Primary text. |
| `--ledger-navy` | `#1B2A4A` | Brand / primary. Nav, primary buttons, headers, focus ring. |
| `--recovered-green` | `#1F7A5C` | Recovered amounts, success states. Confident forest tone, not neon. |
| `--at-risk-amber` | `#B8791E` | At-risk and pending states. Warm, not alarmist. |
| `--stopped-crimson` | `#8C2F39` | **Reserved** for `stop` / `withheld` badges and outright batch failure. Used sparingly, like a stamp. |
| `--simulated-slate` | `#6B7280` | `[SIMULATED]` tags. Deliberately muted so simulated actions visually recede against real ones. |

Defined as CSS custom properties in `frontend/styles/globals.css` and referenced
through `tailwind.config.ts` (`00_CONTRACTS_RevFlow.md` §9). Not duplicated as hex
literals in components.

**Colour is never the only signal.** `[REAL]` and `[SIMULATED]` tags carry text.
The withheld stamp says the word "WITHHELD". A reader with a colour vision
deficiency loses nothing.

### 2.2 Typography — three roles

| Role | Typeface | Usage |
|---|---|---|
| Display | Newsreader (serif) | Page titles and section headers only. Supplies the ledger character; used with restraint. |
| Body / UI | IBM Plex Sans | All UI copy, labels, buttons, nav. Technical but warm; avoids the Inter-everywhere default. |
| Data / Mono | IBM Plex Mono | **All** monetary figures, timestamps, decline codes, event IDs, enum values. |

The mono rule is what makes the ledger metaphor work rather than merely referencing
it. Any figure a reader might compare against another figure is monospaced so the
digits align in a column.

Type scale: 12 / 14 / 16 / 20 / 28 / 40 px. Weights 400, 500, 600 only — no
ultra-bold, per Principle 3.

Fonts are loaded via `next/font/google`, which self-hosts them at build time
(`00_CONTRACTS_RevFlow.md` §10.3). No runtime request to Google Fonts, so the demo
renders correctly offline.

### 2.3 Spacing

4 px base unit: 4, 8, 12, 16, 24, 32, 48, 64. Cards and table rows use 16/24
internal padding; section gaps use 32/48.

### 2.4 Radius and elevation

Radius 6 px throughout — small and serious, neither zero nor bubbly. One elevation
level only, `0 1px 3px rgba(18,22,28,0.08)`, on cards and the drawer. Everything
else is flat, so the ledger reads like paper rather than floating glass.

### 2.5 Motion

150 ms ease-out for hover and expand, 200 ms for the drawer slide-in. No page-load
choreography, no ambient animation. `prefers-reduced-motion: reduce` drops
everything to instant state changes.

---

## 3. Information architecture

Navigation is flat because Phase 0 has no authentication and a single user class
(`04_SRS_RevFlow.md` §2.3, §9). There is no login wall and no nested menu.

```text
┌──────────────────────────────────────────────────────────────┐
│  RevFlow     Overview   Audit Trail   Exceptions  [Run Batch]│
└──────────────────────────────────────────────────────────────┘
```

Three destinations, matching FR-29, FR-30, and FR-31 — the whole product is one
click away. A top bar rather than a sidebar, because three items in a sidebar
wastes horizontal space on a screen full of tabular numbers.

The **Run Batch** button sits top-right, persistent. It is the single most
important action a judge will take, and it calls `POST /run-batch` (FR-35). It is
the only non-GET call the frontend makes anywhere.

Depth is at most two levels — list, then detail drawer — so no breadcrumbs.

---

## 4. Screens

### 4.1 Overview

**Purpose.** Answer "how much did we recover, and can I trust it?" in under five
seconds. This is the first screen a judge sees.

```text
┌───────────────────────────────────────────────────────────────────┐
│  RevFlow      Overview   Audit Trail   Exceptions    [Run Batch]  │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ₹ Recovered            ₹ At Risk            Recovery Rate       │
│  ┌───────────────┐      ┌───────────────┐    ┌───────────────┐    │
│  │  ‹amount›     │      │  ‹amount›     │    │  ‹pct›        │    │
│  │  of ‹amount›  │      │  across ‹n›   │    │  of addressed │    │
│  │  addressable  │      │  events       │    │  ‹pct› covered│    │
│  └───────────────┘      └───────────────┘    └───────────────┘    │
│                                                                   │
│   Recovery by Pipeline                                            │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Checkout drop-off        ████████░░░░░░░░  ‹pct›           │  │
│  │  Subscription / mandate   ██████░░░░░░░░░░  ‹pct›           │  │
│  │  B2B receivables          ────────────────  —  (see note)   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│   Correctly withheld: ‹n› cases    False-positive cost: ‹amount›  │
│   Decided without an LLM call: ‹pct›                              │
│   [ View exceptions → ]                                           │
└───────────────────────────────────────────────────────────────────┘
```

Four things about this layout are requirements rather than choices.

**"Recovery by Pipeline", not "by Module".** The metric is keyed by `event_type`
(`00_CONTRACTS_RevFlow.md` §1). "Module" means a product feature and is never a
metrics dimension or a JSON key. The v1 label invited a JSON shape keyed by module
that no endpoint returns.

**The Recovery Rate card shows coverage beside the rate.** `recovery_rate_realised`
is computed over `addressable_inr` — the value of events where the action was
`retry_now`, the only action that can touch a payment rail. Showing the rate
without `addressable_coverage` implies the system recovers revenue it has no
mechanism to reach (FR-29, NFR-7, `00_CONTRACTS_RevFlow.md` §5.1). The two numbers
travel together, always.

**The B2B bar renders as `—`, not as a percentage.** There is no `retry_now` row for
`b2b_receivable` anywhere in the decision table, so its realised-recovery
denominator is zero and its rate is `null` by design. The bar shows a flat rule and
a short note: *"No payment-rail retry path — B2B recovery is escalation, not
retry."* Rendering `0%` here would claim a failed attempt where no attempt was
possible.

**"Correctly withheld" and "false-positive cost" sit above the fold.** Not behind a
click. This is the honesty signal, and burying it would undersell the only thing
that distinguishes RevFlow from a retry scheduler. "Decided without an LLM call" sits
alongside because it is the boundedness claim in one number
(`01_PRD_RevFlow.md` §9).

### 4.2 Audit Trail

**Purpose.** Let anyone trace any single decision back to its cause and the rule
that authorised it. The ledger metaphor lives here.

```text
┌───────────────────────────────────────────────────────────────────┐
│  RevFlow      Overview   Audit Trail   Exceptions    [Run Batch]  │
├───────────────────────────────────────────────────────────────────┤
│  Filter: [ All pipelines ▾ ] [ All causes ▾ ] [ All actions ▾ ]   │
│          [ All outcomes ▾ ]  [ search event ID ]                  │
├───────────────────────────────────────────────────────────────────┤
│ │ ‹event_id›   subscription_failure     mandate_expired           │
│ │ ‹amount›     → nudge                  [ SIMULATED ]             │
│ │ "‹rationale›"                         rule: ‹rule_fired›        │
│ ├─────────────────────────────────────────────────────────────────│
│ │ ‹event_id›   b2b_receivable           invoice_disputed          │
│ │ ‹amount›     → stop        ╱ WITHHELD ╲                         │
│ │ "‹rationale›"                         rule: ‹rule_fired›        │
│ ├─────────────────────────────────────────────────────────────────│
│ │ ‹event_id›   checkout_dropoff         bank_timeout              │
│ │ ‹amount›     → retry_now   [ REAL ]   ✓ ‹outcome›               │
│ │ "‹rationale›"                         rule: ‹rule_fired›        │
│ └─────────────────────────────────────────────────────────────────│
└───────────────────────────────────────────────────────────────────┘
```

Every row shows event ID, pipeline, cause, amount, action, a `[REAL]` or
`[SIMULATED]` tag (FR-28), the rationale truncated with expansion, the outcome, and
**`rule_fired`**. The rule is on the row rather than only in the drawer because
"which rule authorised this?" is the question a compliance reader asks first, and
requiring a click to answer it makes the ledger feel defensive.

Left vertical rule per row for the register look. Amounts right-aligned in mono.
Sortable by amount, cause, timestamp; filterable by pipeline, cause, action, and
outcome (FR-30). Filter values are populated from `frontend/lib/contracts.ts`, not
typed as strings, so a renamed enum value fails a test instead of silently emptying
a dropdown (`00_CONTRACTS_RevFlow.md` §9).

`stop` rows get the rotated WITHHELD stamp. Clicking any row opens the drawer.

### 4.3 Exceptions

**Purpose.** Surface every `stop` and `escalate_to_human` deliberately, so nothing
is buried (FR-31).

Same visual language as the Audit Trail, sourced from `GET /exceptions`, split into
two clearly headed groups:

**Withheld by policy** — the `stop` cases. The system correctly refused.

**Needs a human** — the `escalate_to_human` cases. The system declined to decide.

Separating these two is worth the extra header, because conflating "we refused on
purpose" with "we couldn't work it out" undersells the first and hides the second.
Each group shows its count, and the two counts must sum to the exceptions total —
FR-31 admits no omissions, and the test asserts the sum against the audit log.

Each "Needs a human" row carries a lightweight **Mark reviewed** control that
toggles **local React state only**. It issues no request and persists nothing. This
is deliberate: a backend write would mean an endpoint that mutates a decision, which
`00_CONTRACTS_RevFlow.md` §7.11 excludes, and would break the append-only guarantee
FR-26 rests on. The control exists so the screen does not read as a permanent
unresolved backlog during a demo, and the specification is explicit that it is
cosmetic so nobody implements it as a write later.

### 4.4 Event Detail Drawer

A slide-in panel from the right (200 ms), not a page. The underlying list stays
visible for context.

Contents: full event metadata; the complete untruncated rationale; `cause_source`
(`rule` or `llm`) so a reader can see which path classified it; `llm_calls_used`;
a mini timeline where the event has multiple audit rows, such as retry attempts
before an escalation; the assigned `ladder_step` for B2B events; and for
PTP-tracked events the promised date with the pause or resume state (FR-19–FR-21).

**The drawer never shows `true_cause`.** `GET /events/{event_id}` omits it from the
response model (FR-4, `00_CONTRACTS_RevFlow.md` §7.8), so there is nothing to
render. Displaying a per-row correct/incorrect marker would leak the answer key into
the surface being evaluated.

Focus is trapped while open and returns to the triggering row on close.

### 4.5 Empty state

```text
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│                      No recovery data yet                         │
│         Run a batch to classify, decide, and recover              │
│              against the synthetic dataset                        │
│                                                                   │
│                        [ Run Batch ]                              │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

Centred, one primary action. An empty screen is an invitation, not a dead end.

---

## 5. User journeys

### 5.1 Judge / evaluator — the primary demo path

1. Lands on **Overview**. Reads recovered against addressable, with coverage
   stated, in about three seconds.
2. Notices "Correctly withheld: ‹n›" and "Decided without an LLM call: ‹pct›" — the
   two claims that separate this from a retry scheduler.
3. Clicks **View exceptions**. Sees a `stop` row with a WITHHELD stamp and the rule
   that produced it.
4. Clicks that row. The drawer shows `llm_calls_used: 0` and
   `rule_fired: hard_stop_cause_in_denylist`.
5. Concludes the restraint is structural rather than described.

Step 4 is the moment the pitch either lands or does not, which is why
`llm_calls_used` is in the drawer at all. It is the one field that cannot be
produced by a well-behaved model — only by the model never having been called.
`01_PRD_RevFlow.md` US-3 is the acceptance story for this journey.

### 5.2 Revenue operations analyst

1. Runs a batch each morning.
2. Reads recovered against at-risk on Overview.
3. Works **Exceptions** — the `escalate_to_human` group is the actual worklist.
4. Opens a B2B row, sees `ladder_step: firm_reminder` and the invoice age, and
   decides whether to call the customer.
5. Never wonders whether the system contacted someone it shouldn't have, because
   every simulated action carries a tag and the contact cap is a stated rule.

### 5.3 Run Batch flow

```text
[ Run Batch ]  →  POST /run-batch  →  202 Accepted
      │
      ├─ button: spinner + "Running…", disabled (prevents double-trigger)
      ├─ stat cards: skeleton bars
      ├─ poll GET /runs until status leaves `running`
      │
      ├─ completed → toast "Batch complete — ‹n› events processed"
      │              → refetch /metrics, /audit-log
      │
      ├─ 409 Conflict → toast "A batch is already running." (amber, not crimson)
      │
      └─ failed → toast, crimson accent border,
                  "Batch run failed. Check API keys in .env and try again."
```

The 409 path exists because concurrent runs would race on `contact_log` and corrupt
the FR-11 cap (`05_System_Architecture_RevFlow.md` §5). Surfacing it as a calm amber
toast rather than an error is correct — the user did nothing wrong, they were early.

---

## 6. Components

| Component | Role | Notes |
|---|---|---|
| `StatCard` | One hero metric | Accepts a `null` value and renders `—` with a reason string. Required for the B2B rate. |
| `PipelineBar` | One labelled horizontal bar | Renders a flat rule when the value is `null`. Never coerces `null` to `0`. |
| `LedgerRow` | One audit row | Left rule, mono amount, action, tag, rationale, `rule_fired`. |
| `ActionTag` | `[REAL]` / `[SIMULATED]` | Text plus colour. FR-28. |
| `WithheldStamp` | The rotated stamp | `stop` rows only. The one flourish. |
| `FilterChip` | One filter control | Options from `contracts.ts`, never string literals. |
| `EventDrawer` | Detail panel | Focus trap; returns focus on close. |
| `Toast` | Transient feedback | Amber default, crimson for genuine failure only. |
| `Skeleton` | Loading placeholder | Shaped like the content it replaces. |

**`StatCard` and `PipelineBar` both take `number | null`.** This is the component-level
expression of NFR-7: a component that cannot represent "undefined" will have a zero
passed to it, and a zero on the B2B bar is a false claim. Typing the prop as
nullable makes the honest case the easy one.

---

## 7. Loading, error, and empty states

### 7.1 Loading

**Run Batch in progress.** Button shows a spinner and "Running…", disabled to
prevent a double trigger. Overview stat cards show skeleton bars matching card
shape, not blank space.

**Table loading.** Skeleton rows — three or four bars shaped like a ledger row.
Never a bare spinner on a data-heavy screen; a spinner gives no sense of what is
coming.

### 7.2 Errors

**Some events could not be processed.** Inline banner at the top of Overview, amber
background (`--at-risk-amber`, not crimson, per Principle 3), plain language:

> *"‹n› events could not be processed. They are in the Audit Trail with outcome
> `api_error`, and the rule that applied is recorded for each."*

**The copy must not offer a retry.** The v1 version read *"retry from Audit Trail"*,
which implies a UI affordance that writes — contradicting the pure-read-layer
decision (§3, `05_System_Architecture_RevFlow.md` §3.6) and the endpoint exclusions
in `00_CONTRACTS_RevFlow.md` §7.11. There is no per-event retry control anywhere in
RevFlow. The corrected copy tells the reader where to look instead of offering an
action that does not exist, which is also the more useful message: an `api_error`
outcome is a recorded decision, not a lost one.

**Batch run failed outright.** Toast with a `--stopped-crimson` accent border — the
reserved-colour exception, since this genuinely is a failure — reading *"Batch run
failed. Check API keys in .env and try again."* Actionable rather than vague. Never a
raw stack trace or bare status code.

**A run is already in progress (409).** Amber toast, *"A batch is already
running."* Not an error.

### 7.3 Empty

**No data yet.** §4.5.

**No exceptions.** *"No exceptions yet — nothing has needed a stop or human
review."* Framed positively; an empty Exceptions screen is a good outcome, and the
copy has to make that legible immediately or a reader will assume the screen is
broken.

*(On the specified dataset this state will not occur — 19 events are guaranteed hard
stops, per `00_CONTRACTS_RevFlow.md` §6.2. The state is specified because a
filtered view can still reach it and because the frontend must not assume a
non-empty response.)*

**Filtered view with no matches.** *"No events match these filters."* with a **Clear
filters** link.

---

## 8. Forms

Two, both minimal, because Phase 0 has no configuration surface
(`04_SRS_RevFlow.md` §9).

**Filter form (Audit Trail).** Four dropdowns — pipeline, cause, action, outcome —
plus an event-ID search. No submit button; filters apply live on change, since this
is low-stakes and instantly reversible. Options come from `contracts.ts`.

**Policy ceiling panel (Overview footer).** Displays `MAX_RETRIES`,
`COOLDOWN_HOURS`, `MAX_CONTACTS_PER_CUSTOMER_PER_DAY`, and the `STOP_IF_CAUSE_IN`
list as **read-only** fields fetched from `GET /config` (FR-36).

Two points on this panel. It is read-only in every phase of Phase 0 — there is no
write endpoint and none is planned, and the v1 description of it as "editable in
Phase 1" was written against roadmap content that no longer exists; per-merchant
tuning is Phase 3 and the hard stops stay non-tunable in every phase
(`03_Roadmap_RevFlow.md` Appendix A). And it reads from the API rather than
displaying literals, so the panel cannot show a threshold the engine no longer uses.
Hardcoding `3` next to the label "Max retries" is the most likely way for this screen
to lie, and FR-36 exists to remove the reason to.

---

## 9. Accessibility

**Contrast.** All text and background pairs meet WCAG AA at 4.5:1 minimum. `--ink`
on `--canvas` is roughly 15:1. Action tags and stamps were checked against
`--canvas` and pass at their specified sizes.

**Colour is never the only signal.** `[REAL]` and `[SIMULATED]` carry text. The
withheld stamp says "WITHHELD". The B2B pipeline bar shows a flat rule plus a text
note, not merely an absence of fill.

**Keyboard navigation.** Every table row, filter chip, and button is reachable by
Tab with a visible 2 px `--ledger-navy` focus ring, never suppressed. The drawer
traps focus while open and returns it to the triggering row on close. Escape closes
the drawer.

**Screen readers.** Stat cards use an `aria-label` combining label and value.
Because amounts are rendered with `en-IN` grouping, the label should spell the value
in words — *"Recovered, two lakh eighty-four thousand six hundred rupees"* — since a
screen reader will otherwise read the grouped digits awkwardly. Where a value is
`null`, the label reads *"Recovery rate for B2B receivables: not applicable, no
payment-rail retry path"* rather than "dash".

**Motion.** All transitions respect `prefers-reduced-motion: reduce` by dropping to
instant state changes.

---

## 10. Responsive behaviour

Desktop widths only — 1280 px and above is the design target, degrading acceptably
to 1024 px. Below that, the layout is not supported and does not pretend to be.

This is a scope decision, stated rather than hidden: RevFlow Phase 0 is a demo
surface shown on a laptop or a shared screen, and spending the ten days on
responsive tables would take them from the guardrail tests. Mobile layouts are
listed in `04_SRS_RevFlow.md` §9 as explicitly out of scope.

---

## 11. Implementation notes

**Number formatting.** All monetary values arrive from the API as integer paise.
Convert and format only at the presentation layer, using
`Intl.NumberFormat('en-IN')` for lakh/crore grouping. `frontend/lib/format.ts` is
the only place this happens (`00_CONTRACTS_RevFlow.md` §10.2). No component does
arithmetic on money.

**No arithmetic in the frontend at all.** Percentages, sums, rates, and counts
arrive computed from `metrics/`. If a screen needs a number the API does not return,
the fix is a metrics change, not a `reduce()` in a component (NFR-7).

**Enum-driven UI.** Filter options, tag colours, and badge conditions derive from
`frontend/lib/contracts.ts`, which mirrors
`backend/revflow/contracts/enums.py` and is asserted equal by a test
(`00_CONTRACTS_RevFlow.md` §9). A new `cause` appears in the filter dropdown with no
frontend edit; a renamed one fails a test instead of silently emptying it.

**Nullable metric props.** `StatCard` and `PipelineBar` accept `number | null`. This
is not defensive typing — it is required for the B2B rate, and the type is what
prevents a well-meaning `?? 0`.

**Tokens as CSS custom properties.** Declared once in `globals.css`, surfaced
through `tailwind.config.ts`. No hex literal appears in a component.

**Fonts self-hosted** via `next/font/google` at build time, so the demo renders
correctly with no network.

**Polling, not websockets.** The Run Batch flow polls `GET /runs`. A websocket would
add a server dependency for a ten-second wait that happens once per demo.

---

**Cross-references used:** `00_CONTRACTS_RevFlow.md` §1, §5.1, §6.2, §7.8, §7.11,
§9, §10.2, §10.3, §12; `01_PRD_RevFlow.md` §9, US-3;
`03_Roadmap_RevFlow.md` Appendix A; `04_SRS_RevFlow.md` §2.3, §9, FR-4, FR-11,
FR-19–FR-21, FR-26, FR-28, FR-29, FR-30, FR-31, FR-35, FR-36, NFR-7;
`05_System_Architecture_RevFlow.md` §3.6, §5; `08_Audit_Report_RevFlow.md`.
All resolve.
