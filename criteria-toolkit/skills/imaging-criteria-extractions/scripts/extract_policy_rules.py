#!/usr/bin/env python3
"""
extract_policy_rules.py  —  Step 0: make the rule-list FIRST

The fix for criteria generation flattening pathways and dropping safety rules:
before writing any criteria, list every rule the policy states. Nothing can be
silently dropped once it's written down up front, and the list is what the
coverage check later diffs against.

This produces a first-pass RULE INVENTORY from the policy text — every coverage
sentence, classified:
  EXCLUSION      — "not covered", "contraindicated", "investigational"
  INDICATION     — "covered when", "reasonable and necessary", "indicated"
  LIMITATION     — frequency/interval limits ("once every 2 years")
  ADMINISTRATIVE — facility/billing/FDA boilerplate (not per-code clinical)
and flags `has_or_group` when the sentence offers alternative routes
("either", "at least one of the following") — i.e. a PATHWAY the generation step
must keep as separate doors, not flatten into one AND-list.

The agent reviews/curates this into the final inventory, then criteria generation
is told to cover every INDICATION/EXCLUSION/LIMITATION item. It is deterministic
(no API) — a starting checklist, not the final word.

Usage:
  python3 extract_policy_rules.py --policy lcd.txt ncd.txt article.txt \
      --out-json rule_inventory.json --out-md rule_inventory.md
"""

import re
import sys
import json
import argparse
from pathlib import Path

# reuse the sentence/signal/admin machinery from the coverage check
sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage_check import sentences, content_terms, SIGNAL, ADMIN, ICD_TOKEN  # noqa: E402

EXCLUSION = re.compile(r"\b(not covered|non-?covered|excluded?|exclusion|contraindicat|"
                       r"investigational|denies coverage|denied|is not (a )?benefit)\b", re.I)
LIMITATION = re.compile(r"\b(once every|every \w+ (year|month|week)|limited to|no more than|"
                        r"not more (often|frequently)|frequency|interval|per \w+ period)\b", re.I)
INDICATION = re.compile(r"\b(covered (when|for|if)|reasonable and necessary|medically necessary|"
                        r"indicated|appropriate|suitable candidate|is a benefit)\b", re.I)
OR_GROUP = re.compile(r"\b(either|at least one of|one of the following|any of the following|"
                      r"following (situations|conditions|indications))\b", re.I)


def classify(s):
    if ADMIN.search(s):
        return "ADMINISTRATIVE"
    if EXCLUSION.search(s):
        return "EXCLUSION"
    if LIMITATION.search(s):
        return "LIMITATION"
    if INDICATION.search(s):
        return "INDICATION"
    return "INDICATION"  # signal matched but unclear -> treat as indication to be safe


def extract(policy_text):
    rules, seen = [], set()
    for s in sentences(policy_text):
        # a rule is any coverage-signal sentence OR one offering alternative routes
        if not (SIGNAL.search(s) or OR_GROUP.search(s)):
            continue
        if len(ICD_TOKEN.findall(s)) >= 3:      # ICD code-table fragment
            continue
        key = s[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        terms = content_terms(s)
        if len(terms) < 3:
            continue
        rules.append({
            "id": f"R{len(rules)+1}",
            "type": classify(s),
            "has_or_group": bool(OR_GROUP.search(s)),
            "text": s,
            "key_terms": sorted(set(terms), key=terms.index)[:10],
        })
    return rules


ORDER = ["INDICATION", "EXCLUSION", "LIMITATION", "ADMINISTRATIVE"]


def to_md(rules):
    out = ["# Policy rule inventory", "",
           "The full list of rules the policy states — the checklist criteria "
           "generation must cover. `[or]` marks alternative routes (keep as "
           "separate pathways, do not flatten).", ""]
    for typ in ORDER:
        group = [r for r in rules if r["type"] == typ]
        if not group:
            continue
        out.append(f"## {typ} ({len(group)})")
        for r in group:
            orflag = " `[or-group → pathway]`" if r["has_or_group"] else ""
            out.append(f"- [ ] **{r['id']}**{orflag} {r['text']}")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract a policy rule inventory (checklist-first)")
    ap.add_argument("--policy", nargs="+", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args(argv)
    text = "\n".join(Path(p).read_text(errors="replace") for p in args.policy)
    rules = extract(text)
    Path(args.out_json).write_text(json.dumps({"rules": rules}, indent=2))
    Path(args.out_md).write_text(to_md(rules))
    from collections import Counter
    ct = Counter(r["type"] for r in rules)
    orn = sum(1 for r in rules if r["has_or_group"])
    print(f"extracted {len(rules)} rules: {dict(ct)}; {orn} with or-groups (pathways). "
          f"wrote {args.out_json}, {args.out_md}", file=sys.stderr)


if __name__ == "__main__":
    main()
