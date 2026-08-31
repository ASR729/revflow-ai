#!/usr/bin/env python3
"""
RevFlow document-set consistency checker.

Run from the folder containing the nine RevFlow markdown documents:

    python3 verify_docs.py

Exits 0 if every check passes, 1 otherwise. Nine checks, described in
08_Audit_Report_RevFlow.md Section 10.1. Re-run after editing any document —
the failure modes this catches are exactly the ones that produced the v1 defects.
"""
import re, sys, glob, os
from collections import defaultdict

DOCS  = sorted(glob.glob("[0-9][0-9]_*.md"))
NINE  = {os.path.basename(d) for d in DOCS}
T     = {os.path.basename(d): open(d, encoding="utf-8").read() for d in DOCS}
fails = defaultdict(list)
def fail(k, msg): fails[k].append(msg)

if len(DOCS) != 9:
    print(f"WARNING: expected 9 documents, found {len(DOCS)}: {sorted(NINE)}\n")

C   = T.get("00_CONTRACTS_RevFlow.md", "")
PRD = T.get("01_PRD_RevFlow.md", "")
SRS = T.get("04_SRS_RevFlow.md", "")
DP  = T.get("07_Development_Plan_RevFlow.md", "")
AUDIT = "08_Audit_Report_RevFlow.md"

# ── heading index ────────────────────────────────────────────────────────────
headings = {}
for d, s in T.items():
    hs = set()
    for m in re.finditer(r"^#{2,4}\s+(?:Appendix\s+([A-Z])|(\d+(?:\.\d+)*)\.?)\s", s, re.M):
        hs.add("Appendix " + m.group(1) if m.group(1) else m.group(2))
    for h in list(hs):
        p = h.split(".")
        for i in range(1, len(p)): hs.add(".".join(p[:i]))
    headings[d] = hs

def section(doc, start, end=None):
    i = doc.find(start)
    if i < 0: return ""
    j = doc.find(end, i) if end else -1
    return doc[i:j] if j > 0 else doc[i:]

# ── 1. cited filenames ───────────────────────────────────────────────────────
print("1. Cited filenames are within the nine-document set")
cited = {(d, m.group(1)) for d, s in T.items()
         for m in re.finditer(r"`?(\d\d_[A-Za-z0-9_]+\.md)`?", s)}
bad    = sorted({(d, f) for d, f in cited if f not in NINE and d != AUDIT})
exempt = sorted({f for d, f in cited if f not in NINE and d == AUDIT})
for d, f in bad: fail(1, f"{d} cites {f}, which is not in the set")
if exempt: print(f"   (exempt: {AUDIT} names phantom files as audit subjects: {exempt})")
print(f"   {'PASS' if not bad else 'FAIL'}: {len({f for _, f in cited})} distinct filenames cited")

# ── 2. FR/NFR ids defined ────────────────────────────────────────────────────
print("2. Every cited FR/NFR is defined in the SRS")
defined = set(re.findall(r"^\| \*\*((?:N?FR)-\d+)\*\*", SRS, re.M))
citedid = defaultdict(set)
for d, s in T.items():
    for m in re.finditer(r"\b((?:N?FR)-\d+)\b", s): citedid[d].add(m.group(1))
allc = set().union(*citedid.values()) if citedid else set()
for u in sorted(allc - defined):
    fail(2, f"{u} cited by {[d for d in citedid if u in citedid[d]]} but not defined in the SRS")
seq = sorted(int(x.split("-")[1]) for x in defined if x.startswith("FR-"))
if seq != list(range(1, len(seq) + 1)): fail(2, f"FR numbering not contiguous: {seq}")
print(f"   {'PASS' if not fails[2] else 'FAIL'}: {len(allc)} cited, {len(defined)} defined, FR-1..FR-{len(seq)} contiguous")

# ── 3. section references resolve ────────────────────────────────────────────
print("3. Cross-document section references resolve to real headings")
pref = {b[:2]: b for b in NINE}
ref  = re.compile(r"`(\d\d)(?:_[A-Za-z0-9_]+\.md)?`?\s*"
                  r"((?:(?:§|Section\s+|Appendix\s+)[A-Z0-9][0-9.]*(?:\s*[–-]\s*[0-9.]+)?"
                  r"(?:\s*,\s*(?:§|Section\s+|Appendix\s+)?[A-Z0-9][0-9.]*(?:\s*[–-]\s*[0-9.]+)?)*))")
n = 0
for d, s in T.items():
    for m in ref.finditer(s):
        tgt = pref.get(m.group(1))
        if not tgt: continue
        for tok in re.finditer(r"(?:§|Section\s+|Appendix\s+)?\s*(Appendix\s+[A-Z]|[0-9]+(?:\.[0-9]+)*)", m.group(2)):
            n += 1
            if tok.group(1) not in headings[tgt]:
                fail(3, f"{d} -> {tgt} §{tok.group(1)} (no such heading)")
print(f"   {'PASS' if not fails[3] else 'FAIL'}: {n} references checked")

# ── 4. enum counts ───────────────────────────────────────────────────────────
print("4. Enum headers match their value counts")
esec, declared = section(C, "## 2. Closed enumerations", "## 3. Database schema"), set()
for m in re.finditer(r"^### 2\.\d+ `(\w+)` — (\d+) values?$", esec, re.M):
    name, want = m.group(1), int(m.group(2))
    blk = esec[m.end():]; nx = re.search(r"^### ", blk, re.M); blk = blk[:nx.start()] if nx else blk
    vals = re.findall(r"^\| `(\w+)`", blk, re.M)
    if not vals:
        vals = re.findall(r"`(\w+)`", next((l for l in blk.split("\n") if l.strip()), ""))
    vals = list(dict.fromkeys(vals)); declared |= set(vals)
    if len(vals) != want: fail(4, f"`{name}` header says {want} values, {len(vals)} listed")
stop = re.findall(r'STOP_IF_CAUSE_IN`?\*?\*?\s*=\s*`?\[([^\]]+)\]', C)
if stop:
    for v in (x.strip().strip('"\'') for x in stop[0].split(",")):
        if v not in declared: fail(4, f"STOP_IF_CAUSE_IN member `{v}` is not a declared cause")
print(f"   {'PASS' if not fails[4] else 'FAIL'}: {len(declared)} values across 11 enums")

# ── 5. no undeclared enum-shaped tokens ──────────────────────────────────────
print("5. No undeclared enum-shaped tokens in other documents")
STRUCT = set(re.findall(r"^\| `(\w+)`", section(C, "## 3. Database schema", "## 4. Policy"), re.M))
STRUCT |= {"insufficient_balance"}  # v1 name; named in the audit report as defect C2
OK = declared | STRUCT | {
 'run_id','event_id','customer_id','event_type','ladder_step','cause_source','true_cause','retry_count',
 'paused_until','promised_date','ptp_status','batch_run_status','simulated_channel','rule_fired',
 'llm_calls_used','invoice_age_days','ladder_step_at_pause','customer_reply_text','decline_code',
 'contact_date','detection_source','batch_runs','audit_log','simulated_actions','ptp_commitments',
 'contact_log','summary_metrics','classifier_metrics','addressable_inr','addressable_coverage',
 'recovery_rate_realised','realised_recovered_inr','at_risk','use_llm','insert_audit_row',
 'assert_test_mode','generate_dataset','run_batch','decline_map','action_table','hard_stops',
 'simulated_comms','razorpay_client','classifier_eval','batch_loader','llm_fallback','voice_script',
 'false_positive_cost','action_breakdown','delete_customer','rzp_test_','prefers_reduced_motion',
 'full_history','synthetic_events','sample_hinglish','color_scheme','next_font'}
bad5 = {(d, m.group(1)) for d, s in T.items() if d != "00_CONTRACTS_RevFlow.md"
        for m in re.finditer(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`", s)
        if m.group(1) not in OK and not m.group(1).endswith(('_py','_ts','_tsx','_md','_json','_sql','_wav','_css'))}
for d, t in sorted(bad5): fail(5, f"{d} uses `{t}`, not declared in contracts §2 or §3")
print(f"   {'PASS' if not bad5 else 'FAIL'}")

# ── 6. config constants / env vars defined ───────────────────────────────────
print("6. Referenced constants are defined in §4.1 or §10.1")
CFG = set(re.findall(r"^\| `([A-Z][A-Z0-9_]+)` \|", C, re.M))
KW  = {'REAL','SIMULATED','WITHHELD','NOT','NULL','AUTOINCREMENT','INTEGER','TEXT','REFERENCES',
       'SELECT','UPDATE','DELETE','INSERT','PATCH','GET','POST','PUT','WHERE','JOIN','GROUP',
       'NEXT_PUBLIC_','YYYYMMDDTHHMMSS','REVFLOW_BUILD_PROMPT','STOP_IF_CAUSE_IN',
       # protocol / status keywords used by the operational documents (09, 10).
       # These are not configuration constants and have no home in §4.1 or §10.1.
       'BLOCKED','PROCEED','COMPLETE','INCOMPLETE','CRITICAL','MAJOR','MINOR',
       'PRESENT','ABSENT','EXTRA','REVIEW'}
used = defaultdict(set)
for d, s in T.items():
    for m in re.finditer(r"`([A-Z][A-Z0-9_]{4,})`", s):
        t = m.group(1)
        if t in KW or t.startswith("SYN_"): continue
        used[t].add(d)
for t in sorted(used):
    if t not in CFG: fail(6, f"`{t}` referenced in {sorted(used[t])} but not defined in §4.1/§10.1")
print(f"   {'PASS' if not fails[6] else 'FAIL'}: {len(CFG)} defined, {len(used)} referenced")

# ── 7/8. task ids ────────────────────────────────────────────────────────────
print("7. Task IDs in the milestone table are defined in the dev plan")
deftask = {f"{a}-{b}" for a, b in re.findall(r"^\| (SET|DB|BE|FE|INT|TEST|BUG|DEP)-(\d+) \|", DP, re.M)}
mm = re.search(r"\| \*\*M1\*\* Foundation.*?\| \*\*M6\*\* Submitted[^\n]*\n", C, re.S)
need = set()
if mm:
    for m in re.finditer(r"\b(SET|DB|BE|FE|INT|TEST|BUG|DEP)-(\d+)(?:\s*[–-]\s*(\d+))?", mm.group(0)):
        a, b = int(m.group(2)), m.group(3)
        for i in range(a, (int(b) if b else a) + 1): need.add(f"{m.group(1)}-{i}")
for t in sorted(need - deftask): fail(7, f"{t} appears in the milestone table but is not defined")
print(f"   {'PASS' if not fails[7] else 'FAIL'}: {len(need)} referenced, {len(deftask)} defined")

print("8. Every task ID cited anywhere is defined in the dev plan")
allt = set()
for s in T.values(): allt |= {f"{a}-{b}" for a, b in re.findall(r"\b(TEST|BUG|DEP|SET|BE|FE|INT|DB)-(\d+)\b", s)}
for t in sorted(allt - deftask, key=lambda x: (x.split('-')[0], int(x.split('-')[1]))):
    fail(8, f"{t} cited but not defined in the dev plan")
print(f"   {'PASS' if not fails[8] else 'FAIL'}: {len(allt)} cited")

# ── 9. user stories ──────────────────────────────────────────────────────────
print("9. Every user-story ID cited anywhere is defined in PRD §7")
usd = set(re.findall(r"^\| (US-\d+) \|", PRD, re.M)); usc = set()
for s in T.values(): usc |= set(re.findall(r"\b(US-\d+)\b", s))
for t in sorted(usc - usd, key=lambda x: int(x.split('-')[1])): fail(9, f"{t} cited but not defined")
print(f"   {'PASS' if not fails[9] else 'FAIL'}: {len(usc)} cited, {len(usd)} defined")

# ── 10. milestone table identical across 00 / 03 / 07 ────────────────────────
print("10. Milestone table is identical in documents 00, 03 and 07")
pat = re.compile(r"\| \*\*M1\*\* Foundation.*?\| \*\*M6\*\* Submitted[^\n]*", re.S)
tabs = {}
for d in ("00_CONTRACTS_RevFlow.md", "03_Roadmap_RevFlow.md", "07_Development_Plan_RevFlow.md"):
    m = pat.search(T.get(d, ""))
    tabs[d] = m.group(0) if m else None
    if not m: fail(10, f"{d} has no milestone table")
uniq = {v for v in tabs.values() if v}
if len(uniq) > 1: fail(10, "milestone tables differ between documents")
print(f"   {'PASS' if not fails[10] else 'FAIL'}")

# ── 11. SRS priorities match contracts §11.1 ─────────────────────────────────
print("11. SRS requirement priorities match contracts §11.1")
canon = {m.group(1): m.group(2).replace("*", "").strip()
         for m in re.finditer(r"^\| ((?:N?FR)-\d+) \| [^|]+\| ([^|]+)\|", C, re.M)}
srsp  = {m.group(1): m.group(3).strip()
         for m in re.finditer(r"^\| \*\*((?:N?FR)-\d+)\*\* \| (.+?) \| ([^|]+) \| ([^|]+) \|\s*$", SRS, re.M)}
for k, v in sorted(srsp.items()):
    if k not in canon: fail(11, f"{k} has no priority in contracts §11.1")
    elif canon[k] != v: fail(11, f"{k}: contracts says {canon[k]}, SRS says {v}")
print(f"   {'PASS' if not fails[11] else 'FAIL'}: {len(srsp)} compared")

# ── summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
tot = sum(len(v) for v in fails.values())
if tot == 0:
    print(f"ALL 11 CHECKS PASS  ({len(DOCS)} documents, "
          f"{sum(len(s.splitlines()) for s in T.values())} lines)")
    sys.exit(0)
print(f"{tot} FINDING(S) ACROSS {len(fails)} CHECK(S)\n")
for k in sorted(fails):
    for f in fails[k]: print(f"  [check {k}] {f}")
sys.exit(1)
