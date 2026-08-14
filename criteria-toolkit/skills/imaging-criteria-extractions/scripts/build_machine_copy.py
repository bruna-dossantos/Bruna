#!/usr/bin/env python3
"""
build_machine_copy.py  —  inline big code sets for the machine (platform) copy

The human review doc keeps the short call-out ("6,458 codes, see file"); the
machine/platform copy needs every code written out so the evaluator (which has no
lookup) can actually check a diagnosis. This produces:
  1. <LCD>_criteria_MACHINE_full_codes.md — the full criteria with any
     `list_not_inlined` criterion's code set injected inline.
  2. <LCD>_group1_dx_codes.txt — the codes as a paste-ready comma-joined block.

Checksums the loaded code count against the criterion's `list_not_inlined.count`
and ABORTS on mismatch — never ship a list that doesn't match the stated total.

Usage:
  build_machine_copy.py criteria.json --codes codes.csv --out-dir <dir>
"""

import re
import csv
import sys
import json
import copy
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_criteria_doc


def load_codes(path):
    rows = list(csv.DictReader(open(path)))
    if rows and "icd10_code" in rows[0]:
        return [(r["icd10_code"].strip(), r.get("description", "").strip()) for r in rows]
    # fallback: first two columns
    raw = list(csv.reader(open(path)))
    start = 1 if raw and not re.match(r"^[A-Z]\d", raw[0][0]) else 0
    return [(r[0].strip(), (r[1] if len(r) > 1 else "").strip()) for r in raw[start:] if r]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build machine copy with inlined code sets")
    ap.add_argument("criteria_json")
    ap.add_argument("--codes", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    doc = json.loads(Path(args.criteria_json).read_text())
    codes = load_codes(args.codes)
    n = len(codes)
    if n != len({c for c, _ in codes}):
        sys.exit(f"ABORT: code file has duplicates ({n} rows, {len({c for c,_ in codes})} distinct)")
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    lcd = doc.get("policy", {}).get("lcd", "policy")

    inline_block = "; ".join(f"{c} — {d}" if d else c for c, d in codes)
    injected = referenced = 0
    written_once = {}  # (list id) -> anchor label; inline the full list only the first time
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    for g in groups:
        for c in g.get("codes", []):
            for ot in (c.get("order_types") or [{"criteria": c.get("criteria", [])}]):
                for cr in ot.get("criteria", []):
                    lni = cr.get("list_not_inlined")
                    if not lni:
                        continue
                    if lni.get("count") and lni["count"] != n:
                        sys.exit(f"ABORT checksum: criterion '{cr.get('title')}' states "
                                 f"{lni['count']} codes but file has {n}. Not shipping.")
                    key = lni.get("what", "codes")
                    if key not in written_once:
                        # first occurrence: write the full list out
                        cr["definition"] = (cr.get("definition", "").rstrip()
                                            + f"\nCovered ICD-10-CM diagnoses (all {n}): "
                                            + inline_block + ".")
                        written_once[key] = f"{c['code']} · {cr.get('title')}"
                        injected += 1
                    else:
                        # later occurrences: reference the one written-out copy (identical set)
                        cr["definition"] = (cr.get("definition", "").rstrip()
                                            + f"\nCovered ICD-10-CM diagnoses (all {n}): the same "
                                            f"set written out under {written_once[key]} "
                                            f"(also in L37373_group1_dx_codes.csv).")
                        referenced += 1
                    cr.pop("list_not_inlined", None)

    # full machine criteria doc
    machine_md = out / f"{lcd}_criteria_MACHINE_full_codes.md"
    machine_md.write_text(render_criteria_doc.render(doc))
    # paste-ready codes block
    codes_txt = out / f"{lcd}_group1_dx_codes.txt"
    codes_txt.write_text(", ".join(c for c, _ in codes) + "\n")

    print(f"codes: {n} (checksum OK) | written out once in {injected} criterion(s), "
          f"referenced in {referenced} more", file=sys.stderr)
    print(f"wrote {machine_md.name} ({machine_md.stat().st_size//1024} KB) and {codes_txt.name}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
