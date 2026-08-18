#!/usr/bin/env python3
"""Sync payer_project_crosswalk.csv between the local cache and the shared Google Sheet.
The Sheet is the shared home: the feedback loop PULLS before applying and PUSHES after. venv python.

  python3 crosswalk_sheets.py push    # local CSV  -> Sheet
  python3 crosswalk_sheets.py pull     # Sheet      -> local CSV
"""
import os, sys, csv, json, shutil, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_io as S

MASTER = os.path.expanduser("~/Claude/Projects/Linear Master Data")
CROSSWALK = os.path.join(MASTER, "payer_project_crosswalk.csv")
POINTERS = os.path.join(MASTER, "reconciliation_sheets.json")
TAB = "Crosswalk"


def _sheet_id():
    return json.load(open(POINTERS))["crosswalk"]


def push():
    sh = S.client().open_by_key(_sheet_id())
    S.write_csv(sh, TAB, CROSSWALK)
    S.delete_default_sheet1(sh)
    n = sum(1 for _ in open(CROSSWALK)) - 1
    print(f"pushed {n} crosswalk rows → Sheet {_sheet_id()} [{TAB}]")


def pull():
    sh = S.client().open_by_key(_sheet_id())
    try:
        rows = S.read_tab(sh, TAB)
    except Exception:
        print("no Crosswalk tab yet — skipping pull (keeping local CSV)"); return
    if not rows or len(rows) < 2:
        print("Sheet crosswalk empty — skipping pull (keeping local CSV)"); return
    shutil.copy(CROSSWALK, CROSSWALK + ".bak_prepull")
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"pulled {len(rows) - 1} crosswalk rows ← Sheet into {CROSSWALK}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["push", "pull"])
    a = ap.parse_args()
    (push if a.action == "push" else pull)()
