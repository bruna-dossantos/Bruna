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


def flagged_criteria(doc):
    groups = doc.get("groups") or [{"codes": doc.get("codes", [])}]
    for g in groups:
        for c in g.get("codes", []):
            for ot in (c.get("order_types") or [{"criteria": c.get("criteria", [])}]):
                for cr in ot.get("criteria", []):
                    if cr.get("list_not_inlined"):
                        yield c, cr


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

    # checksum every flagged criterion against the loaded count before anything ships
    n_flagged = 0
    for _, cr in flagged_criteria(doc):
        n_flagged += 1
        cnt = (cr.get("list_not_inlined") or {}).get("count")
        if cnt and cnt != n:
            sys.exit(f"ABORT checksum: criterion '{cr.get('title')}' states {cnt} codes "
                     f"but file has {n}. Not shipping.")

    codes_only = ", ".join(c for c, _ in codes)
    inline_block = "; ".join(f"{c} — {d}" if d else c for c, d in codes)

    # 1) PLATFORM JSON — full literal set inlined into EVERY flagged criterion, so
    #    each order type is self-contained for an evaluator with no lookup.
    plat = copy.deepcopy(doc)
    for c, cr in flagged_criteria(plat):
        # label from the criterion itself, so a NON-covered (negative-policy) set is
        # never mislabeled "covered".
        what = (cr.get("list_not_inlined") or {}).get("what") or "covered diagnoses"
        cr["definition"] = (cr.get("definition", "").rstrip()
                            + f"\nThe {what} are the following {n} "
                            f"ICD-10-CM codes: {codes_only}.")
        cr.pop("list_not_inlined", None)
    plat_json = out / f"{lcd}_criteria.PLATFORM.json"
    plat_json.write_text(json.dumps(plat, indent=2))

    # 2) MACHINE MD (human-readable) — full list written once + referenced elsewhere,
    #    so the file stays a sane size to skim.
    md = copy.deepcopy(doc)
    injected = referenced = 0
    written_once = {}
    for c, cr in flagged_criteria(md):
        key = (cr.get("list_not_inlined") or {}).get("what", "codes")
        label = key if key != "codes" else "Covered ICD-10-CM diagnoses"
        if key not in written_once:
            cr["definition"] = (cr.get("definition", "").rstrip()
                                + f"\n{label} (all {n}): {inline_block}.")
            written_once[key] = f"{c['code']} · {cr.get('title')}"
            injected += 1
        else:
            cr["definition"] = (cr.get("definition", "").rstrip()
                                + f"\n{label} (all {n}): the same set written "
                                f"out under {written_once[key]} (also in {lcd}_group1_dx_codes.csv).")
            referenced += 1
        cr.pop("list_not_inlined", None)
    machine_md = out / f"{lcd}_criteria_MACHINE_full_codes.md"
    machine_md.write_text(render_criteria_doc.render(md))

    # 3) paste-ready codes block
    codes_txt = out / f"{lcd}_group1_dx_codes.txt"
    codes_txt.write_text(codes_only + "\n")

    print(f"codes: {n} (checksum OK across {n_flagged} covered-dx criteria)", file=sys.stderr)
    print(f"wrote {plat_json.name} ({plat_json.stat().st_size//1024} KB — full list in all "
          f"{n_flagged} criteria), {machine_md.name} ({machine_md.stat().st_size//1024} KB — "
          f"list once, referenced in {referenced}), {codes_txt.name}", file=sys.stderr)


if __name__ == "__main__":
    main()
