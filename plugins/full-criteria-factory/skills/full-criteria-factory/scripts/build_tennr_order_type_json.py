#!/usr/bin/env python3
"""Emit a Tennr platform-ingest JSON for a policy: requiredDocuments + primaryCodes
(one entry per code x order type, criteria with nested extractionFields) + accessoryCodes.

Maps the interchange criteria.json (+ extraction_fields.csv) into the shape Tennr ingests.
MAPPING (flag any you want changed):
- DOCUMENTATION-type criteria  -> requiredDocuments (one custom "Physician Written Order")
- all other criteria           -> primaryCodes[].criteria
- extraction rows (by code+criterion_n) -> that criterion's extractionFields[]
- one primaryCodes entry per (code x order_type); variation = order-type label when a code has >1
- stageTag = "PENDING" (drafts are reviewer PENDING — NOT verified)
- extractionField tag = the modality (best available "where to look" hint)
"""
import argparse, csv, json, os, sys
from collections import defaultdict

DOC_TYPES = {"DOCUMENTATION"}

# Extraction-field tags must come from the platform's fixed vocabulary. Map each
# criterion type to the record type where that concept is documented.
VALID_TAGS = {"Labs", "EMR Info", "Authorization", "Letter of Medical Necessity",
              "Physician Written Order", "Medical Record", "Insurance Verification",
              "Proof of Delivery", "Certification Statement", "Baseline Sleep Study",
              "Titration Sleep Study", "Diagnostic Test Result", "Sleep Study Interpretation",
              "Sample Choice", "Reference Document"}
TYPE_TAG = {
    "PRIOR_IMAGING": "Diagnostic Test Result",
    "METHODOLOGY": "Diagnostic Test Result",
    "CONTRAST": "Diagnostic Test Result",
    "PRIOR_WORKUP": "Diagnostic Test Result",
    "SPECIMEN": "Labs",
    "DOCUMENTATION": "Physician Written Order",
}
def tag_for(ctype):
    return TYPE_TAG.get(ctype, "Medical Record")

def load_extraction(csv_path):
    by = defaultdict(list)  # (code, criterion_n) -> [field,...] (all rows; _g marks grounded)
    if not os.path.exists(csv_path):
        return by
    for r in csv.DictReader(open(csv_path, newline="")):
        key = (r.get("code", ""), str(r.get("criterion_n", "")))
        if r.get("extraction_field") in ("", "(none detected)"):
            continue
        tags = []
        if r.get("modality"):
            tags.append({"name": r["modality"]})
        by[key].append({
            "label": r.get("extraction_field", ""),
            "description": (r.get("directive") or r.get("definition") or "").strip(),
            "tags": tags,
            "_g": bool(r.get("cui") and "|" in (r.get("concept_set") or "")),
        })
    return by

def crit_obj(cr, ext_by, code, modality, prefer_grounded=True, dx_codes=None, authored=None):
    definition = cr.get("definition", "")
    # inline the full covered ICD-10 set into the covered-diagnosis criterion (the one
    # that references the code file via list_not_inlined)
    if cr.get("list_not_inlined") and dx_codes:
        definition = definition.rstrip() + f" Covered ICD-10-CM diagnoses ({len(dx_codes)} codes): " + ", ".join(dx_codes) + "."
    o = {
        "label": cr.get("title", ""),
        "definition": definition,
        "isEnabled": True,
        "lineageId": None,
    }
    tag = [{"name": tag_for(cr.get("type"))}]
    fields = []
    akey = f"{code}::{cr.get('n')}"
    if authored is not None:
        # authored map is the source of truth. AI-authored decision-variable fields are
        # retrieval-only; a criterion missing from the map gets the neutral synth stub below
        # — never the annotator CSV (which carries banned synonym words like "abnormal").
        for x in authored.get(akey, []):
            t = x.get("tag") if x.get("tag") in VALID_TAGS else tag_for(cr.get("type"))
            fields.append({"label": x.get("label", ""), "description": x.get("description", ""), "tags": [{"name": t}]})
    else:
        raw = ext_by.get((code, str(cr.get("n", ""))), [])
        grounded = [f for f in raw if f.get("_g")]
        chosen = (grounded if (prefer_grounded and grounded) else raw)
        fields = [{"label": f["label"], "description": f["description"], "tags": tag} for f in chosen]
    # every clinical criterion must have >=1 extraction field: neutral retrieval-only stub.
    # Deliberately generic (no criterion title) so no threshold/judgment word can leak in via
    # the title; the parent criterion supplies the context.
    if not fields:
        fields = [{
            "label": "Supporting documentation",
            "description": "Find documentation in the medical record relevant to this requirement.",
            "tags": tag,
        }]
    o["extractionFields"] = fields
    return o

def main(argv=None):
    ap = argparse.ArgumentParser(description="Build Tennr order-type ingest JSON from criteria + extraction fields")
    ap.add_argument("criteria_json", help="the resolved criteria.json")
    ap.add_argument("--extraction", help="extraction_fields.csv (for nested extractionFields)")
    ap.add_argument("--codes", help="dx code CSV (icd10_code,description) to inline into the covered-diagnosis criterion")
    ap.add_argument("--authored-fields", help="JSON map of 'code::n' -> [{label,description,tag}] AI-authored extraction fields")
    ap.add_argument("--stage-tag", default="STAGE_NOT_SET", help="stageTag value for each primary code")
    ap.add_argument("--all-fields", action="store_true", help="include ungrounded/noisy extraction fields too (default: grounded only)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    d = json.load(open(args.criteria_json))
    ext_by = load_extraction(args.extraction) if args.extraction else defaultdict(list)
    dx_codes = []
    if args.codes and os.path.exists(args.codes):
        with open(args.codes, newline="") as fh:
            rr = csv.reader(fh)
            next(rr, None)
            dx_codes = [row[0].strip() for row in rr if row and row[0].strip()]
    authored = None
    if args.authored_fields and os.path.exists(args.authored_fields):
        af = json.load(open(args.authored_fields))
        authored = af.get("fields", af) if isinstance(af, dict) else None

    codes = [(g, c) for g in d.get("groups", []) for c in g.get("codes", [])]

    # requiredDocuments: dedupe DOCUMENTATION criteria by title across the policy
    doc_seen, doc_crit = set(), []
    for _, c in codes:
        for ot in c.get("order_types", []):
            for cr in ot.get("criteria", []):
                if cr.get("type") in DOC_TYPES and cr.get("title") not in doc_seen:
                    doc_seen.add(cr.get("title"))
                    doc_crit.append({"label": cr.get("title", ""), "definition": cr.get("definition", ""), "isEnabled": True, "lineageId": None})
    required_documents = []
    if doc_crit:
        required_documents.append({"kind": "custom", "documentType": "Physician Written Order", "criteria": doc_crit})

    # primaryCodes: one entry per (code x order_type)
    primary = []
    for _, c in codes:
        ots = c.get("order_types", [])
        multi = len(ots) > 1
        for ot in ots:
            crits = [crit_obj(cr, ext_by, c["code"], c.get("modality", ""), prefer_grounded=not args.all_fields, dx_codes=dx_codes, authored=authored)
                     for cr in ot.get("criteria", []) if cr.get("type") not in DOC_TYPES]
            primary.append({
                "hcpcsCode": c["code"],
                "stageTag": args.stage_tag,
                "variation": ot.get("order_type") if multi else None,
                "criteria": crits,
            })

    out = {
        "policy": {"lcd": d.get("policy", {}).get("lcd", ""), "title": d.get("policy", {}).get("title", ""),
                   "payer": d.get("policy", {}).get("payer", ""), "reviewer": "PENDING"},
        "requiredDocuments": required_documents,
        "primaryCodes": primary,
        "accessoryCodes": [],
    }
    json.dump(out, open(args.out, "w"), indent=2, ensure_ascii=False)
    print(f"wrote {os.path.basename(args.out)}: {len(primary)} primaryCode/order-type entries, "
          f"{len(required_documents)} requiredDocument group(s)", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
