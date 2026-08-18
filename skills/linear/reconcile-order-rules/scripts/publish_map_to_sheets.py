#!/usr/bin/env python3
"""Publish the per-row map CSV into the shared 'Order Type → Ticket' Sheet, IN PLACE. venv python:
   ~/Claude/Projects/.venv-sheets/bin/python publish_map_to_sheets.py "<Order_Type_Ticket_Map_*.csv>"
Sheet id comes from reconciliation_sheets.json["map"] unless --sheet-id is given.
"""
import os, sys, csv, json, argparse, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_io as S

MASTER = os.path.expanduser("~/Claude/Projects/Linear Master Data")
POINTERS = os.path.join(MASTER, "reconciliation_sheets.json")
TAB = "Order Type → Ticket"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map_csv")
    ap.add_argument("--sheet-id", default=None)
    ap.add_argument("--tab", default=TAB)
    a = ap.parse_args()
    if not os.path.exists(a.map_csv):
        sys.exit(f"ERROR: map CSV not found: {a.map_csv}")
    sid = a.sheet_id or json.load(open(POINTERS))["map"]

    with open(a.map_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    print(f"loaded {len(rows):,} rows × {len(rows[0]) if rows else 0} cols from {a.map_csv}")
    sh = S.client().open_by_key(sid)
    S.write_rows(sh, a.tab, rows)

    ptr = {"sheet_id": sid, "tab": a.tab,
           "url": f"https://docs.google.com/spreadsheets/d/{sid}/edit",
           "rows": len(rows) - 1, "source_csv": os.path.basename(a.map_csv),
           "updated_at": datetime.datetime.now().isoformat(timespec="seconds")}
    with open(os.path.join(MASTER, "map_sheet.json"), "w") as f:
        json.dump(ptr, f, indent=2)
    print(f"✅ published {len(rows) - 1:,} data rows to '{a.tab}' → {ptr['url']}")


if __name__ == "__main__":
    main()
