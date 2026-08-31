# RevFlow — Product Teardown

**Document:** `02_Teardown_RevFlow.md`
**Version:** 2.0
**Status:** Supporting evidence for `01_PRD_RevFlow.md`
**Subject:** Competitive and internal gap analysis justifying RevFlow
**Last updated:** 2026-08-23

**Answers:** *What already exists, and where is the gap?*

**Feeds into:** `01_PRD_RevFlow.md` §2 (the problem) and §5 (module differentiation).
Every whitespace claim in §4 below is mapped to the requirement that makes it real —
a claim in this document with no corresponding requirement is a marketing sentence,
and the mapping table in §4 exists to make that impossible.

> **On the figures in this document.** The market statistics in §1 and §2 are carried
> forward from the source research that motivated RevFlow. They are directionally
> load-bearing for the product argument but **should be re-verified against primary
> sources before any external use** — a pitch, a submission narrative, or a slide.
> Nothing in the build depends on them. Where a figure informs a *design decision*
> rather than just the narrative, that link is stated explicitly, and the only such
> case is the ~70% payment-linked cart abandonment figure, which sets the checkout
> pipeline's cause distribution in `00_CONTRACTS_RevFlow.md` §6.

---

## 1. Why this problem is real, not invented

Approximately **60% of customers abandon a brand entirely after a failed payment** —
they do not retry, they leave. The loss is not the transaction, it is the customer.

On recurring revenue, **UPI Autopay success rates frequently sit at 30–50%**,
materially below card mandate success. Since UPI is India's dominant rail, subscription
businesses in India are leaking revenue *structurally*, not incidentally — the leak is
a property of the rail, so it recurs every billing cycle and compounds.

On the front end, **nearly 70% of cart abandonment in India is payment-linked** rather
than caused by shipping costs or indecision. This is the figure that most directly
contradicts how abandoned-cart tooling behaves: those tools are built on the
assumption that the customer changed their mind. In India, seven times out of ten,
they didn't — the payment step failed them. A tool that responds to a bank timeout
with "still thinking about it?" is answering a question nobody asked.

This figure is the one with a direct build consequence: it sets the proportion of
checkout events in the synthetic dataset that carry a genuine payment failure
(`00_CONTRACTS_RevFlow.md` §6.3), so the dataset reflects the market rather than a
convenient split.

---

## 2. What Razorpay itself has and hasn't shipped

Razorpay launched **Vulcan on 18 August 2026** — a foundation model trained on
nearly 3 trillion data points across 4 billion payments, using around 3,000 signals
per transaction, positioned as a common intelligence layer for routing, fraud
detection, risk assessment, and checkout personalisation.

**Vulcan is prevention infrastructure.** It makes the next attempt more likely to
succeed. It is not a merchant-facing agent that acts on a failure that has already
happened. Those are different problems with different shapes: prevention is a
scoring problem answered before the attempt; recovery is a diagnosis-and-restraint
problem answered after it.

Razorpay's own internal study across 1.5 million shoppers and more than 51,000
businesses found the same payment friction — failed transactions, drop-offs, delays —
surfacing identically from a metro high street to a small-town market. Razorpay is
publicly naming this friction as unsolved.

**RevFlow sits one layer downstream of Vulcan.** Vulcan reduces failures before they
happen; RevFlow recovers the ones that still slip through, and — the part nobody else
does — knows which ones it must not touch. Complementary, not competing. This
positioning matters for the buildathon specifically: RevFlow does not need to
out-predict a 3-trillion-datapoint model, and it does not try to. It occupies the
layer Vulcan explicitly is not.

---

## 3. Global competitive landscape — and where each one stops

| Player | What it does well | Where it stops |
|---|---|---|
| **Stripe Smart Retries** | Free, one-day setup; ML trained on billions of transactions across the Stripe network to optimise retry timing | Card-only, Stripe-only. No B2B receivables. No India/UPI logic. |
| **Chargebee / Recurly** (built-in dunning) | Integrated retry logic inside the subscription platform, for businesses already on that billing stack | Recovery is a feature, not the core product. Subscriptions only — no checkout, no B2B. |
| **Butter Payments** | ML that treats each failed payment individually rather than as batch retry logic; strong DTC and enterprise clients | Historically eCom / Braintree / Recharge. No B2B, no voice, no India rails. |
| **FlyCode** | Adapts per merchant across Stripe, Shopify, Recharge, Skio, Chargebee; genuinely broad B2C **and** B2B recovery | US/Stripe-ecosystem native. No independently verified benchmarks. No SEPA/BACS or non-Western rail support. |
| **Churnkey** | Retention plus dunning stacked on Stripe | **Stacks retries on top of Stripe's own native retries.** Issuers penalise this — over-retrying can lower auth rates and trigger soft blocks. This is precisely the "no stopping rules" failure mode this buildathon explicitly penalises. |
| **Redux, Vindicia, Churn Buster, Paddle Retain, Baremetrics Recover** | Various niches — silent recovery, SMS outreach, enterprise scale | All single-purpose: subscriptions **or** checkout, never either plus B2B. None India-native. None audit-first by design. |

Read the right-hand column as a set and one pattern dominates. Every one of these
tools is optimising **how hard to try**. Not one of them is built around **when to
stop**. Churnkey is the instructive case because its failure mode is not a bug — it
is the logical endpoint of a design that treats more retries as strictly better.
Retry aggression has a ceiling imposed by issuers, and a tool with no concept of
that ceiling will find it the expensive way.

**RevFlow inverts the objective.** Its deterministic hard stop runs *before* any
model is consulted, so restraint is not a parameter that can be tuned upward under
pressure — it is the first thing that executes (`00_CONTRACTS_RevFlow.md` §4.2,
Stage 1). TEST-1 is the executable form of this teardown row: if a revoked mandate
ever reaches a retry, RevFlow has the same defect as Churnkey and the differentiator
is void.

---

## 4. The whitespace RevFlow occupies

No player above combines all five of the following. Each is mapped to the
requirements that implement it, so the claim is checkable rather than assertable.

| # | Whitespace | Why no one holds it | Implemented by |
|---|---|---|---|
| 1 | **One engine across the full leakage funnel** — checkout **and** subscription **and** B2B receivables | Every competitor above is single-purpose | FR-1, FR-8–FR-16; one policy engine, three pipelines (`01_PRD` §5.3) |
| 2 | **India/UPI-native root-cause taxonomy** — NPCI Technical vs. Business Decline framing, mandate-specific failure modes | Every competitor above is card-and-Stripe-native | FR-2, FR-12, FR-13; the `cause` enum (`00_CONTRACTS` §2.2) |
| 3 | **Audit and stopping rules as core architecture, not a bolt-on** | Churnkey's own over-retry problem is the cautionary tale | FR-6, FR-26, FR-27, NFR-1, NFR-2; **TEST-1** |
| 4 | **Regional-language, low-trust-segment outreach** (Hinglish voice) | Zero competitors above address this; answers Razorpay's own finding that friction disproportionately pushes Tier-2/3 first-time shoppers back to cash | FR-22, FR-23; script generation with tone calibrated by cause |
| 5 | **Promise-to-pay tracking married to B2B receivables** | A category none of the subscription-recovery tools touch, since they are consumer-subscription-only | FR-16, FR-18, FR-19, FR-20, FR-21 |

**Item 5 is why promise-to-pay is P0 and not a nice-to-have.** In the v1 document
set this teardown claimed PTP as differentiating whitespace while the PRD listed it
as a P1 that could be cut. That combination is incoherent: it would ship a product
whose stated differentiator was the first thing dropped under time pressure. Settled
at P0 in `00_CONTRACTS_RevFlow.md` §11.1.

**Item 3 is the one that carries the submission.** Items 1, 2, and 4 are scope and
localisation claims — real, but a well-resourced competitor could close them in a
quarter. Item 3 is architectural. A tool built to maximise retry aggression cannot
add principled restraint as a feature flag, because the restraint has to execute
*before* the optimiser to mean anything. That ordering is a rewrite, not a setting.

---

## 5. Verdict

The global market solved subscription dunning for US SaaS on Stripe. Nobody has built
the India-native, audit-first, full-funnel version — and Razorpay told the market
publicly, four days before this buildathon, that this exact friction is still costing
them customers.

The gap is not "recover more". Every tool in §3 recovers more. The gap is a system
that can state its own limits and prove it held them, on Indian rails, across all
three places revenue leaks.

---

**Cross-references used in this document:** `01_PRD_RevFlow.md` §2, §5;
`00_CONTRACTS_RevFlow.md` §2.2, §4.2, §6.3, §11.1. All resolve.
