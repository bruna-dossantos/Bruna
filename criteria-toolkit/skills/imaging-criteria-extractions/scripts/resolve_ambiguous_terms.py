#!/usr/bin/env python3
"""
resolve_ambiguous_terms.py  —  the upstream Ambiguous-Term Resolver (Fix 3 core)

Pins an OPERATIONAL definition of each decisive-but-undefined term INTO the
criterion, so no downstream stage improvises. From the "active SPMS" writeup:
operational definition (the decision: what counts as TRUE, with time window +
treatment + missing-data handling) belongs in the criterion — a dictionary gloss
(UMLS) does not.  Spec: "Ambiguous-Term Resolver — Spec.md".

Two passes (model-in-the-loop, like expand_concepts):
  detect  — deterministic: find decisive lexicon terms in each criterion and flag
            whether the policy already defines them. Emits a worklist.
  apply   — takes model-authored operational-definition objects and embeds an
            inline clause into the matching criterion; escalates unresolved ones.

Usage:
  resolve_ambiguous_terms.py detect criteria.json --out terms.json
  resolve_ambiguous_terms.py apply  criteria.json --resolutions res.json \
      --out criteria.resolved.json --report resolver_report.md
"""

import re
import sys
import json
import argparse
from pathlib import Path

# decisive words that gate qualification but are commonly left undefined
LEXICON = ["active", "stable", "refractory", "significant", "adequate", "unusual",
           "chronic", "acute", "focal", "suspected", "worsening", "progressive",
           "recent", "clinically significant", "significant change", "focal problem"]

# markers that indicate the policy defines the term right there
DEFINED_NEAR = re.compile(r"(means|defined as|i\.e\.|greater than|at least|>\s*\d|"
                          r"\(\s*(>|greater than|≥|at least)|within \w+ (day|week|month|year)|"
                          r"\d+\s*(day|week|month|year))", re.I)


def _iter_criteria(doc):
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    for g in groups:
        for c in g.get("codes", []):
            for ot in (c.get("order_types") or [{"order_type": c.get("description", ""),
                                                 "criteria": c.get("criteria", [])}]):
                for cr in ot.get("criteria", []):
                    yield c, ot, cr


def detect(doc, skip_resolved=False):
    seen, out = set(), []
    for c, ot, cr in _iter_criteria(doc):
        # a criterion that already carries operational definitions is resolved — its
        # injected definition prose contains lexicon words that would re-trigger here.
        if skip_resolved and cr.get("operational_definitions"):
            continue
        defn = cr.get("definition", "")
        low = defn.lower()
        for term in LEXICON:
            m = re.search(rf"\b{re.escape(term)}\b", low)
            if not m:
                continue
            # is it defined nearby (within ~60 chars after the term)?
            window = defn[m.start(): m.start() + 80]
            policy_defined = bool(DEFINED_NEAR.search(window))
            key = (term, cr.get("title", ""))
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "term": term,
                "appears_in": f"{c['code']} · {ot.get('order_type','')} · {cr.get('title','')}",
                "criterion_title": cr.get("title", ""),
                "decisive": True,
                "policy_defined": policy_defined,
                "status": "policy_defined" if policy_defined else "NEEDS_OPERATIONAL_DEFINITION",
                "context": defn[max(0, m.start()-40): m.start()+80].strip(),
            })
    return out


def _clause(od):
    parts = [f'"{od.get("term","")}" means {od["operational_definition"]["rule"]}']
    o = od["operational_definition"]
    if o.get("positives"):
        parts.append("Counts: " + "; ".join(o["positives"]) + ".")
    if o.get("negatives"):
        parts.append("Does not count: " + "; ".join(o["negatives"]) + ".")
    if o.get("time_window"):
        parts.append("Assessed over: " + o["time_window"] + ".")
    if o.get("treatment_handling") and o["treatment_handling"].lower() not in ("n/a", "n/a (imaging)"):
        parts.append("Treatment: " + o["treatment_handling"] + ".")
    if o.get("missing_data_handling"):
        parts.append("If not documented: " + o["missing_data_handling"] + ".")
    return " ".join(parts)


def apply(doc, resolutions):
    by_term = {}
    for r in resolutions:
        by_term.setdefault(r["term"].lower(), []).append(r)
    applied, escalated, defined = [], [], []
    for c, ot, cr in _iter_criteria(doc):
        low = cr.get("definition", "").lower()
        for term, rs in by_term.items():
            if not re.search(rf"\b{re.escape(term)}\b", low):
                continue
            r = rs[0]
            st = r.get("status")
            if st == "policy_defined":
                defined.append((cr.get("title"), r["term"]))
                continue
            if st == "unresolved_escalate":
                cr.setdefault("unresolved_terms", []).append(r["term"])
                escalated.append((cr.get("title"), r["term"]))
                continue
            # resolved_by_interpretation → embed the operational definition
            cr["definition"] = cr.get("definition", "").rstrip() + "\n" + _clause(r)
            cr.setdefault("operational_definitions", []).append(r)
            applied.append((cr.get("title"), r["term"], r.get("provenance", {}).get("reviewer")))
    return applied, escalated, defined


def cmd_detect(args):
    doc = json.loads(Path(args.criteria_json).read_text())
    terms = detect(doc)
    Path(args.out).write_text(json.dumps(terms, indent=2))
    need = [t for t in terms if t["status"] != "policy_defined"]
    print(f"detected {len(terms)} decisive terms | {len(need)} need an operational "
          f"definition | {len(terms)-len(need)} already policy-defined", file=sys.stderr)
    for t in need:
        print(f"  NEEDS DEF: \"{t['term']}\" in {t['criterion_title']}", file=sys.stderr)


def cmd_apply(args):
    doc = json.loads(Path(args.criteria_json).read_text())
    resolutions = json.loads(Path(args.resolutions).read_text())
    applied, escalated, defined = apply(doc, resolutions)
    Path(args.out).write_text(json.dumps(doc, indent=2))
    rep = ["# Ambiguous-term resolver report", "",
           f"- **Operational definitions pinned into criteria:** {len(applied)}",
           f"- **Left alone (policy already defines):** {len(defined)}",
           f"- **Escalated (unresolved — excluded from scoring):** {len(escalated)}", ""]
    if applied:
        from collections import Counter
        distinct = Counter((term, title) for title, term, _ in applied)
        rep.append(f"## Pinned (now decided in the criterion) — {len(distinct)} distinct, "
                   f"applied across {len(applied)} order-type criteria")
        for (term, title), cnt in distinct.items():
            rep.append(f"- **{term}** → {title}  _(in {cnt} order-type criteria; "
                       f"reviewer: PENDING sign-off)_")
        rep.append("")
    if defined:
        rep.append("## Policy-defined (left as-is)")
        for title, term in defined:
            rep.append(f"- **{term}** → {title}")
        rep.append("")
    if escalated:
        rep.append("## Escalated — needs a human decision before this can score")
        for title, term in escalated:
            rep.append(f"- ⚠ **{term}** → {title}")
    Path(args.report).write_text("\n".join(rep))
    print(f"applied {len(applied)} operational definitions, {len(defined)} policy-defined, "
          f"{len(escalated)} escalated; wrote {args.out} and {args.report}", file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(description="Ambiguous-term resolver")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect"); d.add_argument("criteria_json"); d.add_argument("--out", required=True)
    a = sub.add_parser("apply"); a.add_argument("criteria_json")
    a.add_argument("--resolutions", required=True); a.add_argument("--out", required=True)
    a.add_argument("--report", required=True)
    args = p.parse_args(argv)
    {"detect": cmd_detect, "apply": cmd_apply}[args.cmd](args)


if __name__ == "__main__":
    main()
