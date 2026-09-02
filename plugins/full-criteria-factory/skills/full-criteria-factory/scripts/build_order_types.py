#!/usr/bin/env python3
"""
build_order_types.py  —  order types are the qualification unit

Corrects the earlier "pathways = criterion subsets inside a code" model. The real
structure is two levels:

  code + payer/context  ->  ONE OR MORE order types  (the SPLIT level)
  each order type       ->  its OWN criteria set + logic  (AND/OR within the set)

When to split vs keep together:
  - KEEP in one order type (routes OR'd inside its logic_expression) when the
    alternative routes share the SAME documentation + medical-necessity rules
    (e.g. lumbar MRI: red-flag route OR failed-conservative route).
  - SPLIT into separate order types when the criteria SET differs — by lifecycle
    stage (Initial / Continuation / Renewal / Recert / Replacement), diagnosis,
    product, or clinical category (e.g. J1745: Initial-RA vs Continuation-Crohn's).

Input criteria.json may already carry authored `order_types` per code (each with
its own criteria + optional logic_expression + context). If a code only has a flat
`criteria` list, it's wrapped into a single default order type (AND of all criteria)
— correct for diagnostic imaging, where a CPT code is usually one order type.

Also LINTS: flags a code whose single order type mixes split signals (e.g. both
"initial" and "continuation" language), i.e. it probably should be split.

Usage:
  python3 build_order_types.py criteria.json --out criteria.with_order_types.json
"""

import re
import sys
import json
import argparse
from pathlib import Path

LIFECYCLE = {
    "initial": r"\binitial\b", "continuation": r"\bcontinuation|continued\b",
    "renewal": r"\brenewal\b", "recert": r"\brecert", "replacement": r"\breplacement\b",
}


def default_logic(criteria):
    # within one order type, criteria are AND'd (each evaluated on its own; any
    # alternative routes live as OR *inside* a criterion's text)
    return " AND ".join(f"C{c['n']}" for c in criteria) or "—"


def normalize_order_types(code):
    """Return the code's order types as full units, each with criteria + logic."""
    if code.get("order_types"):
        ots = []
        for i, ot in enumerate(code["order_types"], 1):
            crit = ot.get("criteria", [])
            # renumber criteria within the order type if not numbered
            for j, c in enumerate(crit, 1):
                c.setdefault("n", j)
            ots.append({
                "order_type": ot.get("order_type", f"Order type {i}"),
                "context": ot.get("context", {}),
                "criteria": crit,
                "logic_expression": ot.get("logic_expression") or default_logic(crit),
            })
        return ots
    # flat criteria -> one default order type
    crit = code.get("criteria", [])
    label = code.get("description") or "Standard"
    return [{
        "order_type": label,
        "context": {"stage": "n/a", "condition": None, "product": None, "category": None},
        "criteria": crit,
        "logic_expression": code.get("logic_expression") or default_logic(crit),
    }]


def lint(code, order_types):
    warnings = []
    for ot in order_types:
        text = " ".join(c.get("title", "") + " " + c.get("definition", "")
                        for c in ot["criteria"]).lower()
        hits = [name for name, pat in LIFECYCLE.items() if re.search(pat, text)]
        if len([h for h in hits if h in ("initial", "continuation", "renewal", "recert")]) >= 2:
            warnings.append(f"{code['code']} / order type '{ot['order_type']}': mixes "
                            f"{', '.join(hits)} language — likely needs splitting into "
                            f"separate order types (one per lifecycle stage).")
    return warnings


def augment(doc):
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    all_warnings = []
    n_ot = 0
    for g in groups:
        for c in g.get("codes", []):
            ots = normalize_order_types(c)
            c["order_types"] = ots
            c.pop("criteria", None)          # criteria now live under each order type
            c.pop("pathways", None)          # remove the old, wrong representation
            c.pop("qualifies_when", None)
            n_ot += len(ots)
            all_warnings += lint(c, ots)
    return doc, n_ot, all_warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Model order types (the qualification unit)")
    ap.add_argument("criteria_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    doc = json.loads(Path(args.criteria_json).read_text())
    doc, n_ot, warnings = augment(doc)
    Path(args.out).write_text(json.dumps(doc, indent=2))
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    ncode = sum(len(g["codes"]) for g in groups)
    multi = sum(1 for g in groups for c in g["codes"] if len(c["order_types"]) > 1)
    print(f"{ncode} codes -> {n_ot} order types ({multi} codes with >1); wrote {args.out}",
          file=sys.stderr)
    for w in warnings:
        print(f"  [split-lint] {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
