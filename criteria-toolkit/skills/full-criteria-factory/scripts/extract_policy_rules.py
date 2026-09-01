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


# extra administrative signals: revision history, dates, legal/transmittal refs,
# payment/billing, equipment/technique description — NOT patient-qualification rules
ADMIN_EXTRA = re.compile(
    r"\b(revisions? due to|effective \d|\d{2}/\d{2}/\d{2,4}|notice period|transmittal|"
    r"\bTN \d|\bCR\d{3,}|reg\.\s*\d|federal register|payment will be allowed|"
    r"billing and coding|\bMPDI\b|planar image reconstruction|reformatted imaging|"
    r"full market release|market release phase|signal-to-noise|surface (and other )?"
    r"(specialty )?coils|gating devices|pre-?market approval|general guidelines|"
    r"following descriptions|state of the art|separate NCD|sufficient information|"
    r"provided with claims|medicare administrative contractor|\bMAC\b medical|"
    r"CMS (is removing|believes|anticipates)|diagnosis or treatment of the)\b", re.I)

# this policy (L37373) explicitly excludes MRA ("Magnetic Resonance Angiography is
# not addressed"), yet the broad NCD 220.2 drags in MRA/angiography content
OUT_MODALITY = re.compile(r"\b(MRA|angiograph)\b", re.I)

# body regions OUT of scope for a head/neck imaging order type, and IN-scope terms.
# (imaging defaults; a broad national NCD pulls in other-region MRA/MRI content)
OUT_REGION = re.compile(r"\b(chest|thorac|pulmonary|\blung|abdom|pelvi|aort|"
                        r"lower extremit|peripheral arter|renal arter|iliac|breast)\b", re.I)
IN_SCOPE = re.compile(r"\b(head|neck|brain|skull|orbit|spine|spinal|sinus|face|maxillofacial|"
                      r"tmj|jaw|cranial|cervical|intracranial|\bear\b|nasopharyn|oropharyn|"
                      r"temporal|esophag)\b", re.I)


def _deglue(s):
    # PDF extraction glues words ("MedicareAdministrative", "ofMRA"); restore spaces
    # so the classifier's word-boundary patterns match.
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", s)


def relevance(s):
    """clinical (a real in-scope qualification rule) | administrative | out_of_scope."""
    s = _deglue(s)
    if ADMIN.search(s) or ADMIN_EXTRA.search(s):
        return "administrative"
    if OUT_MODALITY.search(s) or (OUT_REGION.search(s) and not IN_SCOPE.search(s)):
        return "out_of_scope"
    return "clinical"


def classify(s):
    s = _deglue(s)
    if ADMIN.search(s) or ADMIN_EXTRA.search(s):
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
            "relevance": relevance(s),   # clinical | administrative | out_of_scope
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
            rel = r.get("relevance", "clinical")
            relflag = "" if rel == "clinical" else f" `[{rel.replace('_', '-')}]`"
            out.append(f"- [ ] **{r['id']}**{orflag}{relflag} {r['text']}")
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
    rel = Counter(r["relevance"] for r in rules)
    orn = sum(1 for r in rules if r["has_or_group"])
    print(f"extracted {len(rules)} rules — relevance: {dict(rel)}; {orn} or-groups. "
          f"({rel['clinical']} clinical rules drive the coverage chips; "
          f"{rel['administrative']} admin + {rel['out_of_scope']} out-of-scope behind the toggle) "
          f"wrote {args.out_json}, {args.out_md}", file=sys.stderr)


if __name__ == "__main__":
    main()
