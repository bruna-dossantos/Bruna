#!/usr/bin/env python3
"""
criterion_view.py  —  split one criterion into POLICY vs CLINICAL CONTEXT.

The resolver folds each operational definition INLINE into the criterion's
`definition` prose (so the strict evaluator sees it). Great for the machine,
but it makes the human doc blend two very different things:

  • POLICY   — what the policy actually requires (verbatim / near-verbatim).
  • CLINICAL — how *we* pinned a vague term so it can be decided (our
               interpretation, `reviewer: PENDING` until a clinician signs off).

This helper reverses the fold for display: it strips each injected clause back
out of the definition (reusing the resolver's own `_clause`, so it always
matches) and returns the clean policy text plus the structured operational
definitions, so a renderer can style them differently.
"""

import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resolve_ambiguous_terms as R  # noqa: E402


def split_criterion(cr):
    """Return (policy_text, op_defs) for a criterion.

    policy_text: the definition with all injected operational-definition clauses
                 removed — the policy requirement on its own.
    op_defs:     the structured operational_definitions list (clinical context).
    """
    definition = cr.get("definition", "") or ""
    # dedup op-defs by term (apply() can append the same one more than once)
    seen, op_defs = set(), []
    for od in (cr.get("operational_definitions", []) or []):
        key = (od.get("term", "") or "").lower()
        if key in seen:
            continue
        seen.add(key)
        op_defs.append(od)
    text = definition
    for od in op_defs:
        clause = R._clause(od)
        # remove the exact injected form ("\n" + clause), then any stray copy
        text = text.replace("\n" + clause, "").replace(clause, "")
        # safety net if the stored prose drifted from _clause(): drop from the
        # '"term" means …' sentence to the end of that clause's known tail.
        term = od.get("term", "")
        if term and f'"{term}" means' in text:
            text = re.sub(rf'\n?"{re.escape(term)}" means.*?(?=\n[A-Z0-9]\.|\n"|\Z)',
                          "", text, flags=re.S)
    return text.strip(), op_defs


def op_def_lines(od):
    """A labeled, human-readable breakdown of one operational definition."""
    o = od.get("operational_definition", {}) or {}
    rows = []
    if o.get("rule"):
        rows.append(("Means", o["rule"]))
    if o.get("positives"):
        rows.append(("Counts", "; ".join(o["positives"])))
    if o.get("negatives"):
        rows.append(("Does NOT count", "; ".join(o["negatives"])))
    if o.get("time_window"):
        rows.append(("Assessed over", o["time_window"]))
    th = o.get("treatment_handling", "")
    if th and th.lower() not in ("n/a", "n/a (imaging)"):
        rows.append(("Treatment", th))
    if o.get("missing_data_handling"):
        rows.append(("If not documented", o["missing_data_handling"]))
    return rows


def reviewer_status(od):
    rev = (od.get("provenance", {}) or {}).get("reviewer")
    return rev if rev else "PENDING"
