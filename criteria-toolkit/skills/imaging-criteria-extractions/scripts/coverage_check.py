#!/usr/bin/env python3
"""
coverage_check.py  —  coverage completeness check

Diffs the generated criteria against the policy's OWN coverage sentences to catch
dropped branches — the failure mode that lost the pacemaker CT-suitability
indication in L37373.

Method (deterministic, no API):
  1. Pull the coverage-relevant sentences from the policy text (those stating an
     indication, limitation, exclusion, or condition — by signal phrase).
  2. For each, measure how much of its distinctive clinical content appears
     anywhere in the generated criteria text.
  3. Rank the least-covered sentences as potential GAPS, listing the specific
     terms that are missing from the criteria.

It flags candidates for human review; it does not decide correctness. A low score
can be a genuine dropped branch (pacemaker) or a sentence the criteria intentionally
omit (e.g. billing boilerplate) — the report says which terms are missing so a
reviewer can judge fast.

Usage:
  python3 coverage_check.py criteria.json --policy policy1.txt [policy2.txt ...] \
      --out coverage_gaps.md
"""

import re
import sys
import json
import argparse
from pathlib import Path

SIGNAL = re.compile(
    r"\b(cover|covered|not covered|reasonable and necessary|medically necessary|"
    r"indicat|limited to|only when|must |contraindicat|exclu|not suitable|"
    r"suitable candidate|appropriate|investigational|noncovered|non-covered|"
    r"denies coverage|denied|required|reasonable)\b", re.I)

STOP = set("""a an the and or of to in for with without on at by is are was were be been being
that this these those which who whom whose when where while as such than then thus into onto from
patient patients used use using effective following situations conditions cases case may can will
shall should would could not no any all some other others its it he she they them their his her
document documented documentation record records medical necessity necessary appropriate given
scan scans study studies imaging image images test testing exam examination coverage covered cover
because due related information section sections provider providers services service claim claims
determination determinations national local include includes including e g i e etc per one two
""".split())

WORD = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")

# Administrative / billing / reference / facility boilerplate — not clinical content.
ADMIN = re.compile(
    r"\b(cms publication|claims processing|social security|title xviii|"
    r"web ?site|web link|mcd|jurisdiction|revision|deleted|cr\d{3,}|"
    r"chapter \d|manual|hospital setting|units|nmr|reference|100-0\d|"
    r"code description change|icd-10-cm code|mobile (ct|unit)|ambulatory|"
    r"freestanding|bureau of radiological|radiation control|market release|"
    r"food and drug administration|\bfda\b|attending physician|maintain a record|"
    r"direct personal supervision|supervision of|full market)\b", re.I)

ICD_TOKEN = re.compile(r"\b[A-TV-Z]\d{2}(\.\d+)?\b")


# Nested list markers (lowercase letter, digit, roman) — sub-items that belong to
# the parent rule. A top-level "A." / "B." (uppercase) starts a NEW rule.
NESTED_MARK = re.compile(r"^(?:[a-z]|[0-9]{1,2}|[ivx]{1,4})[.)]\s")


def sentences(text):
    """
    Segment policy text into coherent rule units. Split only on a real sentence
    period (>=3 word-chars before the '.', a capital after) — never on ':' or a
    list marker like '1.' / 'A.'. Then merge continuations back into their parent
    so enumerations stay whole: a lead-in ending ':', a NESTED marker (a./b./1./2.),
    a short tail, or a lowercase start. Top-level items (A./B./C.) stay separate.
    """
    text = re.sub(r"\s+", " ", text)
    # PDF extraction often glues a sentence end to the next start ("diagnosis.B.");
    # restore a space so glued top-level boundaries can split.
    text = re.sub(r"([a-z]{3})\.([A-Z])", r"\1. \2", text)
    parts = re.split(r"(?<=[A-Za-z0-9]{3})[.]\s+(?=[A-Z])", text)
    merged = []
    for f in (p.strip() for p in parts if p.strip()):
        if merged and (merged[-1].rstrip().endswith(":") or NESTED_MARK.match(f)
                       or len(f) < 40 or f[:1].islower()):
            merged[-1] = merged[-1].rstrip() + " " + f
        else:
            merged.append(f)
    return [m for m in merged if len(m) > 25]


def content_terms(s):
    terms = [w.lower() for w in WORD.findall(s)]
    return [w for w in terms if w not in STOP]


def check(criteria_text, policy_text):
    crit = criteria_text.lower()
    rows = []
    seen = set()
    for s in sentences(policy_text):
        if not SIGNAL.search(s):
            continue
        if ADMIN.search(s):                       # billing/reference boilerplate
            continue
        if len(ICD_TOKEN.findall(s)) >= 3:        # ICD code-table fragment
            continue
        key = s[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        terms = content_terms(s)
        if len(terms) < 3:
            continue
        present = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", crit)]
        missing = [t for t in terms if t not in present]
        score = len(present) / len(terms)
        rows.append({"sentence": s, "score": score,
                     "missing": sorted(set(missing), key=missing.index)[:12]})
    rows.sort(key=lambda r: r["score"])
    return rows


def check_inventory(criteria_text, rules):
    """Diff criteria against a rule inventory (from extract_policy_rules)."""
    crit = criteria_text.lower()
    rows = []
    for r in rules:
        terms = r.get("key_terms") or content_terms(r["text"])
        if not terms:
            continue
        present = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", crit)]
        missing = [t for t in terms if t not in present]
        rows.append({"id": r["id"], "type": r["type"], "has_or_group": r.get("has_or_group"),
                     "sentence": r["text"], "score": len(present) / len(terms),
                     "missing": sorted(set(missing), key=missing.index)[:12]})
    rows.sort(key=lambda x: x["score"])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Coverage completeness check")
    ap.add_argument("criteria_json")
    ap.add_argument("--policy", nargs="*", help="policy text file(s)")
    ap.add_argument("--inventory", help="rule_inventory.json from extract_policy_rules "
                                        "(closes the loop: diff criteria vs the rule list)")
    ap.add_argument("--out", default="coverage_gaps.md")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="flag items with coverage below this (default 0.5)")
    args = ap.parse_args(argv)
    if not args.policy and not args.inventory:
        ap.error("provide --policy and/or --inventory")

    doc = json.loads(Path(args.criteria_json).read_text())
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]

    def all_criteria(code):
        if code.get("order_types"):
            return [cr for ot in code["order_types"] for cr in ot.get("criteria", [])]
        return code.get("criteria", [])

    crit_text = " ".join(
        (cr.get("title", "") + " " + cr.get("definition", ""))
        for g in groups for c in g["codes"] for cr in all_criteria(c))

    if args.inventory:
        rules = json.loads(Path(args.inventory).read_text())["rules"]
        rows = check_inventory(crit_text, rules)
        mode = "rule inventory"
    else:
        policy_text = "\n".join(Path(p).read_text(errors="replace") for p in args.policy)
        rows = check(crit_text, policy_text)
        mode = "policy sentences"
    gaps = [r for r in rows if r["score"] < args.threshold]
    # clinical gaps (exclusion/indication/limitation) are the ones that matter
    clinical_gaps = [r for r in gaps if r.get("type") != "ADMINISTRATIVE"]

    out = [f"# Coverage completeness check — {doc.get('policy',{}).get('lcd','')}",
           f"\nChecked against **{mode}**: {len(rows)} items  |  "
           f"below {args.threshold:.0%}: **{len(gaps)}** "
           f"({len(clinical_gaps)} clinical, {len(gaps)-len(clinical_gaps)} administrative)\n",
           "Ranked least-covered first. 'Missing' = distinctive policy terms absent "
           "from the criteria — a fast pointer to dropped branches. `[or-group]` = a "
           "pathway that must stay a separate route.\n"]
    for r in gaps:
        tag = f" · {r['type']}" if r.get("type") else ""
        orf = " · `[or-group]`" if r.get("has_or_group") else ""
        rid = f"{r['id']} " if r.get("id") else ""
        out.append(f"### {rid}{r['score']:.0%} covered{tag}{orf}")
        out.append(f"> {r['sentence']}")
        out.append(f"**Missing terms:** {', '.join(r['missing']) or '—'}\n")
    Path(args.out).write_text("\n".join(out))
    print(f"checked {len(rows)} items vs {mode}; flagged {len(gaps)} "
          f"({len(clinical_gaps)} clinical) below {args.threshold:.0%}; wrote {args.out}",
          file=sys.stderr)
    for r in clinical_gaps[:6]:
        print(f"  [{r['score']:.0%} {r.get('type','')}] missing: {', '.join(r['missing'][:6])}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
