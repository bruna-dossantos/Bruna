#!/usr/bin/env python3
"""
render_criteria_doc.py  —  Way 2, step 2

Render a criteria JSON (the interchange format the skill produces from the
imaging prompt + criteria-writer) into a "Qualification Criteria by Code"
document, matching the L37373 layout Bruna uploaded.

Output is Markdown (portable, diffable). To hand off a .docx, pipe this through
the `docx` skill, or open the .md and Save As.

Usage:
  python3 render_criteria_doc.py criteria.json > L37373_criteria_by_code.md
"""

import sys
import json
from pathlib import Path

TYPE_LABEL = {
    "CLINICAL_INDICATION": "CLINICAL INDICATION",
    "PRIOR_WORKUP": "PRIOR WORKUP",
    "PRIOR_IMAGING": "PRIOR IMAGING",
    "METHODOLOGY": "METHODOLOGY",
    "CONTRAST": "CONTRAST",
    "THERAPY_LINKAGE": "THERAPY LINKAGE",
    "FREQUENCY": "FREQUENCY",
    "DOCUMENTATION": "DOCUMENTATION",
    "EXCLUSION": "EXCLUSION",
    "SPECIMEN": "SPECIMEN",
}


def render(doc):
    p = doc.get("policy", {})
    out = []
    title = p.get("title", "")
    out.append(f"# Qualification Criteria by Code — LCD {p.get('lcd','')} — {title}".rstrip(" —"))
    if p.get("payer"):
        out.append(f"**Payer:** {p['payer']}")
    if p.get("ncd_baseline"):
        out.append(f"**National baseline:** {p['ncd_baseline']}")
    if p.get("article"):
        out.append(f"**Companion article:** {p['article']}")
    out.append("")
    if p.get("doc_criteria"):
        out.append("## Doc Criteria")
        out.append("_Document types and fields required for this order type (written once, "
                   "covers all codes)._")
        out.append("")
        for d in p["doc_criteria"]:
            out.append(f"### {d['document']}")
            if d.get("description"):
                out.append(f"_{d['description']}_")
            for f in d.get("fields", []):
                out.append(f"- {f}")
            out.append("")
    out.append("## How to read this document")
    out.append("Each code is its own criteria set, and a code qualifies only when every "
               "numbered criterion listed under it is qualified. Each criterion is evaluated "
               "on its own — there is no cross-criterion logic — so every conditional or "
               "exclusion criterion states an explicit pass-through: when its trigger is not "
               "present, the criterion is considered qualified.")
    out.append("")

    groups = doc.get("groups") or [{"group_label": None, "codes": doc.get("codes", [])}]
    for g in groups:
        if g.get("group_label"):
            out.append(f"## {g['group_label']}")
            out.append("")
        for c in g.get("codes", []):
            out.append(f"### {c['code']} — {c.get('description','')}")
            meta = []
            if c.get("modality"):
                meta.append(f"Modality: {c['modality']}")
            if c.get("contrast"):
                meta.append(f"Contrast: {c['contrast']}")
            if meta:
                out.append(" | ".join(meta))
            out.append("")

            order_types = c.get("order_types")
            # backward-compat: a code with a flat criteria list = one order type
            if not order_types and c.get("criteria"):
                order_types = [{"order_type": c.get("description", "Standard"),
                                "criteria": c["criteria"],
                                "logic_expression": None, "context": {}}]

            multi = len(order_types) > 1
            if multi:
                out.append(f"_This code has **{len(order_types)} order types** — separate "
                           f"qualification units, each with its own criteria:_")
                out.append("")
            for ot in order_types:
                if multi:
                    ctx = ot.get("context") or {}
                    ctxbits = ", ".join(str(v) for k, v in ctx.items()
                                        if v and str(v) not in ("n/a", "None"))
                    hdr = f"#### Order Type: {ot['order_type']}"
                    out.append(hdr + (f"  _({ctxbits})_" if ctxbits else ""))
                if ot.get("logic_expression"):
                    out.append(f"*Qualifies when: {ot['logic_expression']}* "
                               f"(each criterion evaluated on its own; OR = alternative routes "
                               f"within this order type).")
                out.append("")
                for cr in ot.get("criteria", []):
                    tag = TYPE_LABEL.get(cr.get("type", ""), cr.get("type", ""))
                    out.append(f"**{cr.get('n','')}. {cr.get('title','')}**  ·  _{tag}_")
                    for line in cr.get("definition", "").split("\n"):
                        out.append(line)
                    if cr.get("source"):
                        out.append(f"> Source: {cr['source']}")
                    out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        sys.exit("usage: render_criteria_doc.py criteria.json")
    doc = json.loads(Path(argv[0]).read_text())
    sys.stdout.write(render(doc))


if __name__ == "__main__":
    main()
