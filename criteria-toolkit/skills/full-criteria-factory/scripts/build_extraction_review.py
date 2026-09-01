#!/usr/bin/env python3
"""Build the extraction-field accept/reject review list for ONE policy.

Reads an <LCD>_extraction_fields.csv and buckets every recall concept by how much
human review it needs, so the ontology-grounded recall sets get an explicit
review/accept surface (not just shipped blind). All fields stay reviewer PENDING.

Buckets:
  must_author  - annotator detected no concept ("(none detected)") -> author a field by hand
  ungrounded   - a concept was detected but did NOT resolve to a UMLS CUI -> sense-check the recall set
  fuzzy_icd    - ICD candidates came from BioPortal fuzzy search (icd_source=bioportal_fuzzy_review) -> verify each code
  grounded_ok  - resolved to a UMLS CUI with atom synonyms (ontology-validated; lowest risk)

Writes <LCD>_extraction_review.md (scannable, must_author + ungrounded inline) and
<LCD>_extraction_review.csv (every non-grounded_ok row, one per line).
Deterministic, offline (reads the CSV only) — safe to run in close_loop's downstream.
"""
import argparse
import csv
import os
import sys


def categorize(r):
    if r.get("extraction_field") == "(none detected)":
        return "must_author"
    if not r.get("cui"):
        return "ungrounded"
    if (r.get("icd_source") or "").strip() == "bioportal_fuzzy_review":
        return "fuzzy_icd"
    return "grounded_ok"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the extraction-field accept/reject review list for one policy")
    ap.add_argument("extraction_fields_csv")
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args(argv)

    if not os.path.exists(args.extraction_fields_csv):
        print(f"[warn] no extraction CSV at {args.extraction_fields_csv}; skipping review list", file=sys.stderr)
        return 0

    cnt = {"must_author": 0, "ungrounded": 0, "fuzzy_icd": 0, "grounded_ok": 0}
    review = []
    with open(args.extraction_fields_csv, newline="") as fh:
        for r in csv.DictReader(fh):
            cat = categorize(r)
            cnt[cat] += 1
            if cat != "grounded_ok":
                review.append({
                    "category": cat, "code": r.get("code", ""),
                    "criterion_n": r.get("criterion_n", ""), "criterion_title": r.get("criterion_title", ""),
                    "extraction_field": r.get("extraction_field", ""), "seed_term": r.get("seed_term", ""),
                    "grounded_label": r.get("grounded_label", ""), "cui": r.get("cui", ""),
                    "concept_set": r.get("concept_set", ""),
                    "icd10_candidates": r.get("icd10_candidates", ""), "icd_source": r.get("icd_source", ""),
                })

    with open(args.out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["category", "code", "criterion_n", "criterion_title",
            "extraction_field", "seed_term", "grounded_label", "cui", "concept_set",
            "icd10_candidates", "icd_source"])
        w.writeheader()
        for row in review:
            w.writerow(row)

    total = sum(cnt.values())
    md = []
    md.append("# Extraction-Field Review List — accept/reject worklist")
    md.append("")
    md.append("Every recall concept was grounded against UMLS/BioPortal. Rows are bucketed by how much human")
    md.append("review they need. All extraction fields remain **reviewer: PENDING** regardless of bucket.")
    md.append("")
    md.append(f"- **Total rows:** {total}")
    md.append(f"- **grounded_ok** (UMLS CUI + atom synonyms — lowest risk): {cnt['grounded_ok']}")
    md.append(f"- **fuzzy_icd** (ICD from BioPortal fuzzy search — verify each code): {cnt['fuzzy_icd']}")
    md.append(f"- **ungrounded** (detected but no UMLS CUI — sense-check): {cnt['ungrounded']}")
    md.append(f"- **must_author** (no concept detected — author by hand): {cnt['must_author']}")
    md.append("")
    md.append("Full row-by-row list (every non-grounded_ok row) is in the companion `_extraction_review.csv`.")

    def bucket(name, cat):
        rows = [r for r in review if r["category"] == cat]
        md.append("")
        md.append(f"## {name} ({len(rows)})")
        if not rows:
            md.append("_none_")
            return
        md.append("")
        md.append("| code | criterion | field | seed term |")
        md.append("|------|-----------|-------|-----------|")
        for r in rows:
            md.append(f"| {r['code']} | {r['criterion_n']}. {r['criterion_title'][:40]} | {r['extraction_field']} | {r['seed_term'][:40]} |")

    bucket("MUST AUTHOR — no concept detected", "must_author")
    bucket("UNGROUNDED — detected but no UMLS CUI", "ungrounded")

    open(args.out_md, "w").write("\n".join(md))
    print(f"wrote {os.path.basename(args.out_md)} + {os.path.basename(args.out_csv)} "
          f"(total {total}: grounded_ok {cnt['grounded_ok']}, fuzzy_icd {cnt['fuzzy_icd']}, "
          f"ungrounded {cnt['ungrounded']}, must_author {cnt['must_author']})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
