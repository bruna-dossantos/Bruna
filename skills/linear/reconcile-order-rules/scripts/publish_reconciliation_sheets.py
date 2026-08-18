#!/usr/bin/env python3
"""Publish reconcile outputs to their shared Google Sheets. venv python:
   ~/Claude/Projects/.venv-sheets/bin/python publish_reconciliation_sheets.py

  • Payer Mapping — Needs Review   (latest Payer_Mapping_Needs_Review_*.csv → 'Needs Review' tab)
  • Ticket Actions                 (latest Ticket_Actions_*.csv → a tab per verdict)
  • Payer Project Crosswalk        (payer_project_crosswalk.csv → 'Crosswalk' tab)
The per-row Order Type → Ticket map is published separately by publish_map_to_sheets.py.
"""
import os, sys, csv, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_io as S
import crosswalk_sheets as X

CU = os.path.expanduser("~/Claude/Projects/Criteria Updates")
MASTER = os.path.expanduser("~/Claude/Projects/Linear Master Data")
POINTERS = os.path.join(MASTER, "reconciliation_sheets.json")
ACTION_TABS = [("FLIP", "FLIP → Done"), ("NEW-TIX", "NEW-TIX → create"),
               ("CONFLICT", "CONFLICT → review"), ("UNIT-GAP", "UNIT-GAP")]


def _latest(pat):
    fs = sorted(glob.glob(os.path.join(CU, pat)))
    return fs[-1] if fs else None


def main():
    ptr = json.load(open(POINTERS))
    gc = S.client()

    nr = _latest("Payer_Mapping_Needs_Review_*.csv")
    if nr:
        sh = gc.open_by_key(ptr["needs_review"])
        S.write_csv(sh, "Needs Review", nr)
        S.delete_default_sheet1(sh)
        print(f"✅ needs-review → {os.path.basename(nr)} → {ptr['needs_review']}")

    ta = _latest("Ticket_Actions_*.csv")
    if ta:
        with open(ta, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        hdr, vi = rows[0], rows[0].index("verdict")
        sh = gc.open_by_key(ptr["ticket_actions"])
        for verdict, tab in ACTION_TABS:
            sub = [hdr] + [r for r in rows[1:] if r[vi] == verdict]
            S.write_rows(sh, tab, sub)
            print(f"   {tab}: {len(sub) - 1} rows")
        S.delete_default_sheet1(sh)
        print(f"✅ ticket-actions → {os.path.basename(ta)} → {ptr['ticket_actions']}")

    X.push()  # crosswalk → its Sheet


if __name__ == "__main__":
    main()
