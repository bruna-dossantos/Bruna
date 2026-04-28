#!/usr/bin/env python3
"""Create customer (child) tickets under each parent.

Reads:
  ~/Desktop/Customers/<name>/input.csv
  ~/Desktop/Customers/<name>/payor_matches.csv
  ~/Desktop/Customers/<name>/code_titles.csv (optional)
  ~/Desktop/Customers/<name>/customer_config.json
  ~/Desktop/Customers/<name>/parents_created.csv
  ~/Desktop/Customers/<name>/existing_parents.csv (optional)
  ~/Desktop/Linear Master Data/<team>_team_labels.csv

Writes:
  ~/Desktop/Customers/<name>/customer_tickets_created.csv  (resumable tracker)

Each customer ticket:
  - lives in cfg["customer_project_id"]
  - has parentId = matching parent ticket UUID
  - carries payor label (DME-team-scoped) + service line label
  - title = "Cxxxx - <description>"

Resumable, dedup key = (Project UUID, Parent UUID, Code, CSV Payor).

Usage:
  python3 create_customer_tickets.py "Comfort Medical"
  python3 create_customer_tickets.py "Comfort Medical" --sleep 1.5
  python3 create_customer_tickets.py "Comfort Medical" --start 0 --limit 2500
"""
import argparse
import csv
import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import (customer_dir, load_config, team_labels_path,
                  workflow_states_path, get_token, gql_with_retry,
                  CUSTOMER_ESTIMATE)

MUTATION = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier url }
  }
}"""


def create_issue(payload, token):
    data = gql_with_retry(MUTATION, {"input": payload}, token)
    ic = data["issueCreate"]
    if not ic["success"]:
        raise RuntimeError(f"issueCreate.success=false: {ic}")
    iss = ic["issue"]
    return iss["id"], iss["identifier"], iss["url"]


def load_parent_lookup(cdir):
    """(Project UUID, Code) → Parent Issue UUID. Includes both freshly
    created parents and any pre-existing ones the user maps in."""
    out = {}
    for fname, code_col, uuid_col in [
        ("parents_created.csv", "Code", "Issue UUID"),
        ("existing_parents.csv", "Code", "Issue UUID"),  # optional
    ]:
        path = os.path.join(cdir, fname)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            out[(r["Project UUID"], r[code_col])] = r[uuid_col]
    return out


def load_payor_matches(cdir):
    out = {}
    for r in csv.DictReader(open(os.path.join(cdir, "payor_matches.csv"))):
        out[r["CSV Payor"].strip()] = {
            "matched": r["Matched Project"].strip(),
            "uuid": r["Project UUID"].strip(),
        }
    return out


def load_titles(cdir):
    p = os.path.join(cdir, "code_titles.csv")
    if not os.path.exists(p):
        return {}
    return {r["Code"].strip(): r["Title"].strip()
            for r in csv.DictReader(open(p))}


def load_team_labels(team):
    out = {}
    with open(team_labels_path(team)) as f:
        for r in csv.DictReader(f):
            out[r["Name"].strip().lower()] = r["UUID"].strip()
    return out


def state_uuid_for(team_full, state_name="Not Started"):
    for r in csv.DictReader(open(workflow_states_path())):
        if r["Team"] == team_full and r["Name"] == state_name:
            return r["UUID"], r["TeamUUID"]
    sys.exit(f"missing {state_name} state for {team_full}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=1.5)
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    cfg  = load_config(args.customer_name)
    team_full = {"dme":"DME Criteria","infusion":"Infusion Criteria"}[cfg["team"]]

    parents = load_parent_lookup(cdir)
    matches = load_payor_matches(cdir)
    titles  = load_titles(cdir)
    labels  = load_team_labels(cfg["team"])
    state_id, team_uuid = state_uuid_for(team_full)
    cust_proj = cfg["customer_project_id"]

    print(f"loaded {len(parents)} parents, {len(matches)} payor matches, "
          f"{len(labels)} team labels", file=sys.stderr)

    token = get_token()
    tracker = os.path.join(cdir, "customer_tickets_created.csv")
    done = set()
    if os.path.exists(tracker):
        for r in csv.DictReader(open(tracker)):
            done.add((r["Project UUID"], r["Parent Issue UUID"],
                      r["Code"], r["CSV Payor"]))
        print(f"Resume: {len(done)} customer tickets in tracker",
              file=sys.stderr)

    rows = []
    in_path = os.path.join(cdir, "input.csv")
    with open(in_path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    end = len(rows) if args.limit is None else min(len(rows),
                                                   args.start + args.limit)
    window = rows[args.start:end]
    print(f"Window: rows {args.start}..{end-1} ({len(window)} rows of {len(rows)})",
          file=sys.stderr)

    new = not os.path.exists(tracker)
    tf = open(tracker, "a", newline="")
    fields = ["CSV Payor", "Matched Project", "Code", "Title",
              "Project UUID", "Parent Issue UUID",
              "Customer Issue UUID", "Customer Issue ID", "URL",
              "Priority", "Volume"]
    w = csv.DictWriter(tf, fieldnames=fields)
    if new:
        w.writeheader(); tf.flush()

    created = skipped = failed = 0
    miss_parent = miss_label = 0
    t0 = time.time()
    for i, r in enumerate(window, 1):
        payor = r.get("CSV Payor", "").strip()
        code  = r.get("Code", "").strip()
        sl    = r.get("Service Line", "").strip()
        try:
            vol = int(float(r.get("Volume", "0") or "0"))
        except ValueError:
            vol = 0
        try:
            prio = int(r.get("Priority")) if r.get("Priority") else 3
        except ValueError:
            prio = 3
        m = matches.get(payor)
        if not m or not m["uuid"]:
            failed += 1
            continue
        proj = m["uuid"]
        parent = parents.get((proj, code))
        if not parent:
            miss_parent += 1
            print(f"  MISS PARENT [{i}] {m['matched']}/{code}", file=sys.stderr)
            continue
        key = (proj, parent, code, payor)
        if key in done:
            skipped += 1
            continue

        payor_label = labels.get(m["matched"].lower(), "")
        sl_label    = labels.get(sl.lower(), "") if sl else ""
        if not payor_label:
            miss_label += 1
            print(f"  MISS LABEL [{i}] {m['matched']!r}", file=sys.stderr)
            continue

        title = titles.get(code) or code
        payload = {
            "title":     title,
            "teamId":    team_uuid,
            "projectId": cust_proj,
            "parentId":  parent,
            "labelIds":  [x for x in (payor_label, sl_label) if x],
            "stateId":   state_id,
            "priority":  prio,
            "estimate":  CUSTOMER_ESTIMATE,
        }
        try:
            uuid, ident, url = create_issue(payload, token)
            w.writerow({
                "CSV Payor": payor,
                "Matched Project": m["matched"],
                "Code": code,
                "Title": title,
                "Project UUID": proj,
                "Parent Issue UUID": parent,
                "Customer Issue UUID": uuid,
                "Customer Issue ID": ident,
                "URL": url,
                "Priority": prio,
                "Volume": vol,
            })
            tf.flush(); os.fsync(tf.fileno())
            done.add(key)
            created += 1
            if created % 25 == 0:
                el = time.time() - t0
                rate = created / el * 60
                eta = (len(window) - i) / max(rate / 60, 0.01) / 60
                print(f"  [{i}/{len(window)}] {ident} (rate={rate:.0f}/min, "
                      f"ETA {eta:.1f}m)", file=sys.stderr)
            time.sleep(args.sleep)
        except Exception as e:
            failed += 1
            print(f"  FAIL [{i}] {payor} {code}: {e}", file=sys.stderr)
            time.sleep(2)

    tf.close()
    el = time.time() - t0
    print(f"\nDone. created={created} skipped={skipped} failed={failed} "
          f"miss_parent={miss_parent} miss_label={miss_label} "
          f"elapsed={el/60:.1f}m", file=sys.stderr)


if __name__ == "__main__":
    main()
