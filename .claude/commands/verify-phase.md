---
description: Run the full verification protocol for a phase and report evidence
argument-hint: <phase number>
---

Run the complete verification protocol for **Phase $1** of the RevFlow build.

Do not report a conclusion you have not evidenced. For every item below, show the
command you ran and its **actual output**. "Tests pass" is not evidence; a pytest
summary line is evidence.

## 1. Re-read the contract

Re-read the sections of `docs/00_CONTRACTS_RevFlow.md` that Phase $1 implements
against. State which sections and line ranges you read. Do this now, in this session,
regardless of what you believe you already know.

## 2. Definition of done

Open `docs/07_Development_Plan_RevFlow.md` §3 and quote the "Definition of done"
column for every task ID in Phase $1. Assess each one individually.

## 3. Automated checks

```bash
python scripts/verify_docs.py     # docs must still be self-consistent
bash scripts/guard_check.sh       # prohibited packages, key prefix, .env history, hardcoded numbers
python -m pytest backend/tests -v # every test that exists so far
git status --short                # nothing unexpected; docs/ untouched
git diff --stat                   # scope of this phase's changes
```

## 4. Contract audit by fresh eyes

Launch the `contract-verifier` subagent for Phase $1. Include its verdict verbatim.
Do not summarise away a finding.

## 5. Fix, then re-verify

If anything failed: fix it, then **re-run this entire protocol from step 3**. Do not
report a phase as complete on the strength of a run that predates your fix.

If you cannot fix something, write a `BLOCKED` entry in `PROGRESS.md` giving the file,
the contract section you consulted, and the precise question — then stop and tell me.
Do not implement a simpler alternative.

## 6. Report

```
## Phase $1 — verification report

Contract sections re-read: <list>

| Check | Command | Result | Evidence |
|---|---|---|---|

Contract-verifier verdict: <verbatim>

Definition of done, per task:
| Task ID | DoD (quoted from 07 §3) | Met? | Evidence |
|---|---|---|---|

Assumptions I made: <list, or "none">
Files created or modified: <list>
Blocked: <list, or "none">

Phase $1 status: COMPLETE | INCOMPLETE
```

Then update `PROGRESS.md` and **stop**. Do not begin the next phase. Wait for me to
reply `PROCEED`.
