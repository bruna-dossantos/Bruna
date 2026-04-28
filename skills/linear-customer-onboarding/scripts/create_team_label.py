#!/usr/bin/env python3
"""Create new team-scoped labels for the customer's team.

Use when build_parent_plan.py reports labels missing from the team CSV.
Creates them in the appropriate team (DME Criteria or Infusion Criteria,
based on the customer's config) and appends to the master labels CSV so
subsequent runs find them by name.

Reads:
  ~/Desktop/Customers/<name>/customer_config.json
  ~/Desktop/Linear Master Data/teams.csv
  ~/Desktop/Linear Master Data/<team>_team_labels.csv

Writes:
  appends to ~/Desktop/Linear Master Data/<team>_team_labels.csv

Usage:
  python3 create_team_label.py "Comfort Medical" --names "New Payor 1" "New Payor 2"
  python3 create_team_label.py "Comfort Medical" --from-file /tmp/missing.txt
"""
import argparse
import csv
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import (customer_dir, load_config, team_labels_path, MASTER_DIR,
                  get_token, gql_with_retry)

MUTATION = """
mutation IssueLabelCreate($input: IssueLabelCreateInput!) {
  issueLabelCreate(input: $input) {
    success
    issueLabel { id name }
  }
}"""


def create_label(name, team_id, token):
    data = gql_with_retry(MUTATION,
                          {"input": {"name": name, "teamId": team_id}}, token)
    ic = data["issueLabelCreate"]
    if not ic["success"]:
        raise RuntimeError(f"issueLabelCreate.success=false: {ic}")
    return ic["issueLabel"]["id"]


def lookup_team_id(team_full_name):
    p = os.path.join(MASTER_DIR, "teams.csv")
    for r in csv.DictReader(open(p)):
        if r["Name"] == team_full_name:
            return r["UUID"]
    sys.exit(f"team {team_full_name!r} not found in teams.csv — "
             f"refresh master data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    ap.add_argument("--names", nargs="+", help="Label names to create")
    ap.add_argument("--from-file", help="Path to file with one label per line")
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    if not args.names and not args.from_file:
        sys.exit("provide --names or --from-file")

    names = list(args.names or [])
    if args.from_file:
        with open(args.from_file) as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    names.append(ln)

    cfg = load_config(args.customer_name)
    team_full = {"dme":"DME Criteria",
                 "infusion":"Infusion Criteria"}[cfg["team"]]
    team_id = lookup_team_id(team_full)

    # Read existing labels for this team to dedupe
    csv_path = team_labels_path(cfg["team"])
    existing = {}
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            existing[r["Name"].strip().lower()] = r["UUID"].strip()

    # Append new labels
    token = get_token()
    new_rows = []
    created = 0
    skipped = 0
    failed  = 0
    for name in names:
        if name.strip().lower() in existing:
            print(f"  skip (exists): {name} → {existing[name.strip().lower()]}",
                  file=sys.stderr)
            skipped += 1
            continue
        try:
            uuid = create_label(name, team_id, token)
            new_rows.append({"Name": name, "UUID": uuid})
            existing[name.strip().lower()] = uuid
            created += 1
            print(f"  + {name} → {uuid}", file=sys.stderr)
            time.sleep(args.sleep)
        except Exception as e:
            failed += 1
            print(f"  FAIL {name}: {e}", file=sys.stderr)
            time.sleep(2)

    if new_rows:
        with open(csv_path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["Name", "UUID"])
            for r in new_rows:
                w.writerow(r)
        print(f"\nappended {len(new_rows)} rows to {csv_path}", file=sys.stderr)
    print(f"created={created} skipped={skipped} failed={failed}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
