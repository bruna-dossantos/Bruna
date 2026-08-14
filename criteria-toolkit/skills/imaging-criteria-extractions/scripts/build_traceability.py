#!/usr/bin/env python3
"""
build_traceability.py  —  rule inventory → criteria, with coverage + linkage

Ties the whole loop together for review: for every rule in the policy rule
inventory (the Step-0 checklist), record whether the generated criteria cover it,
and WHICH criteria it became (best token-overlap matches). Output feeds the
interactive traceability HTML.

Usage:
  python3 build_traceability.py rule_inventory.json criteria.json --out traceability.json
"""

import re
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage_check import content_terms  # noqa: E402

COVERED, PARTIAL = 0.7, 0.4


def flatten_criteria(doc):
    out = []
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    for g in groups:
        for c in g["codes"]:
            units = c.get("order_types") or [{"order_type": c.get("description", ""),
                                              "criteria": c.get("criteria", [])}]
            for ot in units:
                for cr in ot.get("criteria", []):
                    out.append({
                        "code": c["code"], "order_type": ot.get("order_type", ""),
                        "n": cr.get("n", ""), "title": cr.get("title", ""),
                        "type": cr.get("type", ""), "definition": cr.get("definition", ""),
                        "source": cr.get("source", ""),
                        "_terms": set(content_terms(cr.get("title", "") + " " + cr.get("definition", ""))),
                    })
    return out


def build(inv, criteria_doc):
    crits = flatten_criteria(criteria_doc)
    crit_union = " ".join((" ".join(c["_terms"])) for c in crits)
    rows = []
    for r in inv["rules"]:
        terms = r.get("key_terms") or content_terms(r["text"])
        tset = set(terms)
        present = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", crit_union)]
        score = len(present) / len(terms) if terms else 0
        status = "covered" if score >= COVERED else "partial" if score >= PARTIAL else "gap"
        # link to the specific criteria that best match this rule
        links = []
        for c in crits:
            if not tset:
                continue
            overlap = len(tset & c["_terms"]) / len(tset)
            if overlap >= 0.3:
                links.append({"code": c["code"], "order_type": c["order_type"],
                              "n": c["n"], "title": c["title"], "type": c["type"],
                              "definition": c["definition"], "source": c["source"],
                              "match": round(overlap, 2)})
        links.sort(key=lambda x: -x["match"])
        # dedup identical criteria (same title/def repeated across codes) keeping best
        seen, uniq = set(), []
        for l in links:
            k = (l["title"], l["definition"][:60])
            if k not in seen:
                seen.add(k); uniq.append(l)
        rows.append({"id": r["id"], "type": r["type"], "has_or_group": r.get("has_or_group", False),
                     "text": r["text"], "coverage": round(score, 2), "status": status,
                     "missing_terms": [t for t in terms if t not in present][:12],
                     "became": uniq[:6]})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rule→criteria traceability")
    ap.add_argument("rule_inventory")
    ap.add_argument("criteria_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    inv = json.loads(Path(args.rule_inventory).read_text())
    doc = json.loads(Path(args.criteria_json).read_text())
    rows = build(inv, doc)
    Path(args.out).write_text(json.dumps({"rules": rows}, indent=2))
    from collections import Counter
    ct = Counter(r["status"] for r in rows)
    clin = [r for r in rows if r["type"] != "ADMINISTRATIVE"]
    clin_ct = Counter(r["status"] for r in clin)
    print(f"{len(rows)} rules → {dict(ct)}; clinical only: {dict(clin_ct)}; wrote {args.out}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
