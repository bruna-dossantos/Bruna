#!/usr/bin/env python3
"""
build_extraction_fields.py  —  Way 2, steps 3 & 4

From a criteria JSON, produce the corresponding extraction fields — the "go find"
directives Tennr needs to pull evidence from a chart — one row per clinical
concept detected in each criterion, as a CSV.

Pipeline per criterion:
  step 3  — BioPortal Annotator detects the clinical concepts in the criterion
            text (each grounds to a real SNOMED/NCIT class).
  step 4  — emit an extraction-field row per concept: a directive, the seed term,
            the grounded label, ICD-10 candidates (for indication/exclusion
            criteria), and an initial concept_set = [seed]. Rows tagged for
            expansion are the ILLUSTRATIVE ones the model should widen via
            `expand_concepts.py` (Way 1) before shipping.

This is the "right now" path: a deterministic first-pass CSV a human reviews and
then enriches on the flagged rows. It does not invent synonyms itself (raw
ontology expansion underdelivers — see the recall demo); it hands the reviewer a
grounded skeleton plus the exact rows worth an LLM-proposed expansion.

Usage:
  python3 build_extraction_fields.py criteria.json --out extraction_fields.csv
"""

import re
import sys
import csv
import json
import argparse
from pathlib import Path

# import the shared UMLS/BioPortal clients — bundled locally in this skill's scripts/
_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
from bioportal_client import BioPortalClient          # noqa: E402
from expand_concepts import ConceptExpander           # noqa: E402

# criterion types whose concepts are diagnosis-like -> worth ICD-10 candidates
DX_TYPES = {"CLINICAL_INDICATION", "EXCLUSION", "PRIOR_WORKUP", "PRIOR_IMAGING"}

# structural (non-ontology) attributes an extraction field also needs to catch
STRUCTURAL_PATTERNS = [
    ("duration_threshold", r"(greater than|more than|at least|>=?)\s+\w+\s+(day|week|month|year)s?"),
    ("recency_window",     r"within\s+\w+\s+(day|week|month|year)s?"),
    ("frequency_interval", r"(once\s+every|every)\s+\w+\s+(day|week|month|year)s?"),
    ("contrast_status",    r"\b(with(out)?\s+(and\s+with\s+)?contrast|w/o dye|w/dye)\b"),
    ("prior_treatment",    r"\b(conservative treatment|physical therapy|failed|not responding to|medical therapy)\b"),
]

CLINICAL_SEMANTIC_TYPES = "T047,T184,T191,T037,T019,T060,T033,T046,T023"

FIELDS = [
    "code", "modality", "order_type", "criterion_n", "criterion_type", "criterion_title",
    "extraction_field", "directive", "seed_term", "ontology", "grounded_label",
    "class_id", "cui", "concept_set", "definition", "definition_source",
    "icd10_candidates", "icd_source", "needs_review", "source_criterion",
]


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]


def make_directive(label, concept_terms):
    """
    Write the extraction directive so it names the concept AND the ways it can
    surface in a chart — the recall list is the point of the field, so it belongs
    in the instruction, e.g.:
      "Find documentation of Dizziness in the medical record. This can be
       represented in a variety of ways, examples include: dizziness, vertigo,
       lightheadedness, disequilibrium, presyncope, unsteadiness, etc."
    """
    reps, seen = [], set()
    for t in concept_terms:
        t = (t or "").strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            reps.append(t)
    base = f"Find documentation of {label} in the medical record."
    if reps:
        return base + (" This can be represented in a variety of ways, examples "
                       f"include: {', '.join(reps)}, etc.")
    return base


def structural_fields(defn):
    """Detect non-ontology recall targets (timing, frequency, contrast, prior tx)."""
    found = []
    low = defn.lower()
    for name, pat in STRUCTURAL_PATTERNS:
        m = re.search(pat, low)
        if m:
            found.append((name, m.group(0)))
    return found


def _field_templates(defn, ctype, bp, exp):
    """
    The concept/structural fields for a criterion depend only on its definition
    text and type — not the code. Compute once; callers stamp code-specific
    columns. Returns a list of partial-row dicts (no code/modality/criterion_n).
    """
    templates = []
    seen_fields = set()
    try:
        concepts = bp.detect(defn, semantic_types=CLINICAL_SEMANTIC_TYPES)
    except Exception as e:
        concepts = []
        print(f"  [warn] detect failed: {e}", file=sys.stderr)
    for con in concepts:
        surf = con["surfaces"][0]
        label = con["label"] or surf
        field = _slug(label)
        if field in seen_fields:
            continue
        seen_fields.add(field)
        # UMLS atoms = authoritative synonym set (+ ICD) for this concept
        cui = None
        terms = [surf]
        icd = []
        icd_src = ""
        definition = ""
        def_src = ""
        try:
            cs = exp.atoms_concept_set(label)
            cui = cs["cui"]
            terms = cs["match_terms"] or [surf]
            icd = cs["icd10_candidates"] if ctype in DX_TYPES else []
            icd_src = cs.get("icd_source") or "" if ctype in DX_TYPES else ""
            definition = cs.get("definition") or ""
            def_src = cs.get("definition_source") or ""
        except Exception as e:
            print(f"  [warn] atoms failed for '{label}': {e}", file=sys.stderr)
        templates.append({
            "extraction_field": field,
            "directive": make_directive(label, terms),
            "seed_term": surf, "ontology": con["ontology"],
            "grounded_label": con["label"], "class_id": con["class_id"].split("/")[-1],
            "cui": cui or "",
            "concept_set": "|".join(terms),
            "definition": definition, "definition_source": def_src,
            "icd10_candidates": "|".join(icd), "icd_source": icd_src,
            "needs_review": "no",
        })
    for name, snippet in structural_fields(defn):
        if name in seen_fields:
            continue
        seen_fields.add(name)
        templates.append({
            "extraction_field": name,
            "directive": f"Find whether the record documents: {snippet}.",
            "seed_term": snippet, "ontology": "", "grounded_label": "",
            "class_id": "", "cui": "", "concept_set": "", "definition": "",
            "definition_source": "", "icd10_candidates": "", "icd_source": "",
            "needs_review": "no",
        })
    if not templates:
        templates.append({
            "extraction_field": "(none detected)",
            "directive": "No ontology concept or structural attribute detected — author a field manually.",
            "seed_term": "", "ontology": "", "grounded_label": "", "class_id": "",
            "cui": "", "concept_set": "", "definition": "", "definition_source": "",
            "icd10_candidates": "", "icd_source": "", "needs_review": "yes",
        })
    return templates


def build_rows(doc):
    bp = BioPortalClient()
    exp = ConceptExpander()
    rows = []
    cache = {}  # (ctype, defn) -> field templates; many codes share criteria
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    for g in groups:
        for c in g.get("codes", []):
            # criteria live under order_types; fall back to a flat criteria list
            units = c.get("order_types") or [{"order_type": c.get("description", ""),
                                              "criteria": c.get("criteria", [])}]
            for ot in units:
                for cr in ot.get("criteria", []):
                    key = (cr.get("type", ""), cr.get("definition", ""))
                    if key not in cache:
                        cache[key] = _field_templates(cr.get("definition", ""),
                                                      cr.get("type", ""), bp, exp)
                    for tmpl in cache[key]:
                        rows.append({
                            "code": c["code"], "modality": c.get("modality", ""),
                            "order_type": ot.get("order_type", ""),
                            "criterion_n": cr.get("n", ""), "criterion_type": cr.get("type", ""),
                            "criterion_title": cr.get("title", ""),
                            "source_criterion": cr.get("title", ""),
                            **tmpl,
                        })
    print(f"  ({len(cache)} distinct criteria analyzed, {len(rows)} rows emitted)", file=sys.stderr)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build extraction fields from criteria JSON")
    ap.add_argument("criteria_json")
    ap.add_argument("--out", default="extraction_fields.csv")
    args = ap.parse_args(argv)

    doc = json.loads(Path(args.criteria_json).read_text())
    rows = build_rows(doc)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    with_syn = sum(1 for r in rows if "|" in r["concept_set"])
    with_icd = sum(1 for r in rows if r["icd10_candidates"])
    print(f"wrote {len(rows)} extraction-field rows to {args.out}", file=sys.stderr)
    print(f"  {with_syn} rows have UMLS-atom synonym sets; {with_icd} have ICD-10 candidates",
          file=sys.stderr)


if __name__ == "__main__":
    main()
