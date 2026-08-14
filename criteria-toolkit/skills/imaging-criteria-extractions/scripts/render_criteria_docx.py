#!/usr/bin/env python3
"""
render_criteria_docx.py  —  criteria .docx in the Tennr house template (SKILL Step 6)

Matches the format of the exemplar
`Criteria Updates/E0470 Nevada Medicaid — Checklist Format.docx`:
  - metadata table (Service Line, Plan Category, Policy Source, HCPCS Codes Covered)
  - Doc Criteria section
  - per code/order type: a colored SECTION BANNER, then each criterion as a badged
    block with a light header row, □ checklist sub-items, and an italic gray
    left-border policy-quote callout with its Source
  - "APPENDIX — Full Policy Language" on its own page

Requires python-docx (isolated venv if system Python is externally managed).

Usage:
  .venv/bin/python render_criteria_docx.py criteria.json --out criteria.docx
"""

import sys
import json
import argparse
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_BREAK

BANNER = "2E5FA3"       # section banner fill
BANNER2 = "1F3864"      # exclusions / secondary segment
HEADER = "E8F0FB"       # criterion header row fill
GRAY = RGBColor(0x66, 0x66, 0x66)
BOX = "□"          # □

TYPE_LABEL = {"CLINICAL_INDICATION": "CLINICAL INDICATION", "PRIOR_WORKUP": "PRIOR WORKUP",
              "PRIOR_IMAGING": "PRIOR IMAGING", "METHODOLOGY": "METHODOLOGY", "CONTRAST": "CONTRAST",
              "THERAPY_LINKAGE": "THERAPY LINKAGE", "FREQUENCY": "FREQUENCY",
              "DOCUMENTATION": "DOCUMENTATION", "EXCLUSION": "EXCLUSION", "SPECIMEN": "SPECIMEN"}


def _shade(cell, fill):
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def _no_borders(tbl):
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "nil"); borders.append(e)
    tblPr.append(borders)


def banner(doc, text, fill=BANNER):
    t = doc.add_table(rows=1, cols=1); t.autofit = True; _no_borders(t)
    c = t.rows[0].cells[0]; _shade(c, fill)
    p = c.paragraphs[0]; r = p.add_run(text); r.bold = True
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); r.font.size = Pt(11)
    doc.add_paragraph()
    return t


def header_row(doc, badge, title, ctype):
    t = doc.add_table(rows=1, cols=1); t.autofit = True; _no_borders(t)
    c = t.rows[0].cells[0]; _shade(c, HEADER)
    p = c.paragraphs[0]
    b = p.add_run(f"{badge}   "); b.bold = True; b.font.size = Pt(11)
    r = p.add_run(title); r.bold = True; r.font.size = Pt(11)
    tag = p.add_run(f"    ·  {TYPE_LABEL.get(ctype, ctype)}")
    tag.font.size = Pt(8); tag.font.color.rgb = GRAY


def checklist(doc, definition):
    for line in [l for l in definition.split("\n") if l.strip()]:
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.25)
        p.add_run(f"{BOX}  {line.strip()}")


def callout(doc, text):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.2)
    # left border
    pPr = p._p.get_or_add_pPr(); pbdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "8"), ("w:color", BANNER)):
        left.set(qn(k), v)
    pbdr.append(left); pPr.append(pbdr)
    r = p.add_run(text); r.italic = True; r.font.color.rgb = GRAY; r.font.size = Pt(9)


def _codes(doc_json):
    groups = doc_json.get("groups") or [{"group_label": None, "codes": doc_json.get("codes", [])}]
    return [(g.get("group_label"), c) for g in groups for c in g["codes"]]


def build(doc_json, out):
    d = Document()
    p = doc_json.get("policy", {})
    title = d.add_heading(f"Qualification Criteria by Code — LCD {p.get('lcd','')}", level=0)
    d.add_paragraph(p.get("title", ""))

    codes = [c["code"] for _, c in _codes(doc_json)]
    meta = [("Service Line", "Imaging / Radiology — CT & MRI, Head and Neck"),
            ("Plan Category", "MEDICARE"),
            ("Policy Source", f"LCD {p.get('lcd','')}; {p.get('ncd_baseline','')}; "
                              f"{p.get('article','')}"),
            ("HCPCS Codes Covered", ", ".join(codes))]
    mt = d.add_table(rows=len(meta), cols=2); mt.style = "Light Grid Accent 1"
    for i, (k, v) in enumerate(meta):
        mt.rows[i].cells[0].paragraphs[0].add_run(k).bold = True
        mt.rows[i].cells[1].text = v

    if p.get("doc_criteria"):
        d.add_heading("Doc Criteria", level=1)
        for dc in p["doc_criteria"]:
            d.add_heading(dc["document"], level=2)
            if dc.get("description"):
                d.add_paragraph(dc["description"]).runs[0].italic = True
            for f in dc.get("fields", []):
                d.add_paragraph(f, style="List Bullet")

    d.add_heading("Criteria by Code", level=1)
    last_group = None
    for group_label, c in _codes(doc_json):
        if group_label and group_label != last_group:
            d.add_heading(group_label, level=1); last_group = group_label
        d.add_heading(f"{c['code']} — {c.get('description','')}", level=2)
        m = " | ".join(x for x in [f"Modality: {c.get('modality','')}" if c.get("modality") else "",
                                   f"Contrast: {c.get('contrast','')}" if c.get("contrast") else ""] if x)
        if m:
            d.add_paragraph(m)
        ots = c.get("order_types") or [{"order_type": c.get("description", "Standard"),
                                        "criteria": c.get("criteria", []), "logic_expression": None}]
        for oi, ot in enumerate(ots):
            fill = BANNER2 if (ot.get("criteria") and all(cr.get("type") == "EXCLUSION"
                              for cr in ot["criteria"])) else BANNER
            label = ot.get("order_type", "Qualification")
            logic = ot.get("logic_expression")
            banner(d, f"{label}" + (f"  —  Qualifies when: {logic}" if logic else ""), fill)
            crits = ot.get("criteria", [])
            for ci, cr in enumerate(crits):
                header_row(d, str(cr.get("n", ci + 1)), cr.get("title", ""), cr.get("type", ""))
                checklist(d, cr.get("definition", ""))
                if cr.get("source"):
                    callout(d, f"Source: {cr['source']}")
                if ci < len(crits) - 1:
                    conn = d.add_paragraph(); rr = conn.add_run("AND"); rr.bold = True

    # Appendix — full policy language
    d.add_page_break()
    d.add_heading("APPENDIX — Full Policy Language", level=1)
    for group_label, c in _codes(doc_json):
        for ot in (c.get("order_types") or [{"order_type": "", "criteria": c.get("criteria", [])}]):
            for cr in ot.get("criteria", []):
                h = d.add_paragraph()
                h.add_run(f"{c['code']} · {ot.get('order_type','')} · "
                          f"{cr.get('n','')}. {cr.get('title','')}").bold = True
                for line in cr.get("definition", "").split("\n"):
                    if line.strip():
                        d.add_paragraph(line.strip())
                if cr.get("source"):
                    sp = d.add_paragraph(); sr = sp.add_run(f"Source: {cr['source']}")
                    sr.italic = True; sr.font.color.rgb = GRAY; sr.font.size = Pt(9)

    d.save(out)
    return len(codes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render criteria JSON to Tennr-format .docx")
    ap.add_argument("criteria_json"); ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    n = build(json.loads(Path(args.criteria_json).read_text()), args.out)
    print(f"wrote {args.out} ({n} codes, Tennr house format)", file=sys.stderr)


if __name__ == "__main__":
    main()
