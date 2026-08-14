#!/usr/bin/env python3
"""
render_criteria_pdf.py  —  criteria as a clean PDF for Tennr auto-generation

Renders the order-type criteria JSON into a PDF that reads like a policy/criteria
document — the artifact you hand to Tennr to auto-generate criteria from. Same
content as the .docx: metadata, Doc Criteria, per-code order types with criteria
and verbatim Source citations.

Requires reportlab (isolated venv if system Python is externally managed):
  python3 -m venv .venv && .venv/bin/pip install reportlab

Usage:
  .venv/bin/python render_criteria_pdf.py criteria.json --out criteria.pdf
"""

import sys
import json
import argparse
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, ListFlowable, ListItem)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import criterion_view as V  # noqa: E402

POL = colors.HexColor("#2c5cc5")
CLI = colors.HexColor("#b7791f")
CLIBG = colors.HexColor("#fbf1de")

TYPE_LABEL = {
    "CLINICAL_INDICATION": "CLINICAL INDICATION", "PRIOR_WORKUP": "PRIOR WORKUP",
    "PRIOR_IMAGING": "PRIOR IMAGING", "METHODOLOGY": "METHODOLOGY", "CONTRAST": "CONTRAST",
    "THERAPY_LINKAGE": "THERAPY LINKAGE", "FREQUENCY": "FREQUENCY",
    "DOCUMENTATION": "DOCUMENTATION", "EXCLUSION": "EXCLUSION", "SPECIMEN": "SPECIMEN",
}


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(doc, out):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Src", parent=styles["Normal"], fontSize=8,
                              textColor=colors.grey, leftIndent=12, spaceAfter=6))
    styles.add(ParagraphStyle("Crit", parent=styles["Normal"], fontSize=10,
                              spaceBefore=6, spaceAfter=2))
    styles.add(ParagraphStyle("Logic", parent=styles["Normal"], fontSize=9,
                              textColor=colors.HexColor("#333333"), spaceAfter=4))
    styles.add(ParagraphStyle("PolCap", parent=styles["Normal"], fontSize=7.5,
                              textColor=POL, spaceBefore=3, spaceAfter=1))
    styles.add(ParagraphStyle("CliHd", parent=styles["Normal"], fontSize=8.5,
                              textColor=CLI, spaceBefore=2))
    styles.add(ParagraphStyle("CliRow", parent=styles["Normal"], fontSize=8.5, leftIndent=4))
    h1, h2, h3 = styles["Heading1"], styles["Heading2"], styles["Heading3"]
    body = styles["BodyText"]

    def clinical_flow(od):
        """Amber-shaded one-cell table = our interpretation of a vague term."""
        rows = [[Paragraph(f'🩺 <b>CLINICAL INTERPRETATION</b> — how we read '
                           f'"{_esc(od.get("term",""))}" '
                           f'<font size=7 color="#666666">(reviewer {_esc(V.reviewer_status(od))})</font>',
                           styles["CliHd"])]]
        for label, val in V.op_def_lines(od):
            rows.append([Paragraph(f'<b><font color="#b7791f">{_esc(label)}:</font></b> {_esc(val)}',
                                   styles["CliRow"])])
        t = Table(rows, colWidths=[6.3 * inch])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CLIBG),
                               ("LINEBEFORE", (0, 0), (0, -1), 2, CLI),
                               ("TOPPADDING", (0, 0), (-1, -1), 2),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                               ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        return t

    p = doc.get("policy", {})
    story = [Paragraph(f"Qualification Criteria by Code — LCD {_esc(p.get('lcd',''))}", styles["Title"]),
             Paragraph(_esc(p.get("title", "")), styles["Heading2"]),
             Paragraph('<b>How to read this:</b> <font color="#2c5cc5">bulleted items and the blue Source '
                       'line are the POLICY requirement.</font> <font color="#b7791f">Amber 🩺 blocks are '
                       "Tennr's CLINICAL INTERPRETATION of a vague term (reviewer PENDING — a clinician "
                       'signs off before go-live).</font>', body),
             Spacer(1, 8)]

    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    codes = [c["code"] for g in groups for c in g["codes"]]
    meta = [["Service Line", "Imaging / Radiology"],
            ["Policy Source", _esc(f"LCD {p.get('lcd','')}; {p.get('ncd_baseline','')}; {p.get('article','')}")],
            ["Payer", _esc(p.get("payer", ""))],
            ["HCPCS Codes Covered", _esc(", ".join(codes))]]
    tbl = Table([[Paragraph(f"<b>{k}</b>", body), Paragraph(v, body)] for k, v in meta],
                colWidths=[1.6 * inch, 4.9 * inch])
    tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                             ("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f2f2"))]))
    story += [tbl, Spacer(1, 12)]

    if p.get("doc_criteria"):
        story.append(Paragraph("Doc Criteria", h1))
        for dc in p["doc_criteria"]:
            story.append(Paragraph(_esc(dc["document"]), h3))
            if dc.get("description"):
                story.append(Paragraph(f"<i>{_esc(dc['description'])}</i>", body))
            story.append(ListFlowable([ListItem(Paragraph(_esc(f), body)) for f in dc.get("fields", [])],
                                      bulletType="bullet"))

    story.append(Paragraph("Criteria by Code", h1))
    last_group = None
    for g in groups:
        for c in g["codes"]:
            gl = g.get("group_label")
            if gl and gl != last_group:
                story.append(Paragraph(_esc(gl), h1)); last_group = gl
            story.append(Paragraph(f"{_esc(c['code'])} — {_esc(c.get('description',''))}", h2))
            m = " | ".join(x for x in [f"Modality: {c.get('modality','')}" if c.get("modality") else "",
                                       f"Contrast: {c.get('contrast','')}" if c.get("contrast") else ""] if x)
            if m:
                story.append(Paragraph(_esc(m), body))
            ots = c.get("order_types") or [{"order_type": c.get("description", ""),
                                            "criteria": c.get("criteria", []), "logic_expression": None}]
            multi = len(ots) > 1
            if multi:
                story.append(Paragraph(f"<b>This code has {len(ots)} order types — separate "
                                       f"qualification units, each with its own criteria.</b>", body))
            for ot in ots:
                if multi:
                    story.append(Paragraph(f"Order Type: {_esc(ot['order_type'])}", h3))
                if ot.get("logic_expression"):
                    story.append(Paragraph(f"<i>Qualifies when: {_esc(ot['logic_expression'])}</i>", styles["Logic"]))
                for cr in ot.get("criteria", []):
                    story.append(Paragraph(
                        f"<b>{cr.get('n','')}. {_esc(cr.get('title',''))}</b> &nbsp;·&nbsp; "
                        f"<font size=8>{TYPE_LABEL.get(cr.get('type',''), cr.get('type',''))}</font>",
                        styles["Crit"]))
                    policy_text, op_defs = V.split_criterion(cr)
                    story.append(Paragraph("📄 POLICY REQUIREMENT", styles["PolCap"]))
                    for line in policy_text.split("\n"):
                        if line.strip():
                            story.append(Paragraph(_esc(line), body))
                    if cr.get("source"):
                        story.append(Paragraph(f"<i>Source: {_esc(cr['source'])}</i>", styles["Src"]))
                    for od in op_defs:
                        story.append(clinical_flow(od))
                        story.append(Spacer(1, 4))

    SimpleDocTemplate(out, pagesize=letter, topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                      leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                      title=f"L{p.get('lcd','')} Criteria").build(story)
    return len(codes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render criteria JSON to PDF")
    ap.add_argument("criteria_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    doc = json.loads(Path(args.criteria_json).read_text())
    n = build(doc, args.out)
    print(f"wrote {args.out} ({n} codes)", file=sys.stderr)


if __name__ == "__main__":
    main()
