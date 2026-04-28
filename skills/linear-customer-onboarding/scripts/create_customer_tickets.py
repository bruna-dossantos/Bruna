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
  - **inherits the parent's workflow state** — i.e., if the parent is
    "In Progress" because someone has already started writing criteria
    for it, the customer ticket starts in "In Progress" too. Falls back
    to the team's "Not Started" state when the parent's state isn't
    recorded (older tracker files that pre-date this column).
  - carries payor label (DME-team-scoped) + service line label
  - title = "<HCPCS> - <description>"  (e.g. "A4351 - Indwelling Catheter")

Resumable, local dedup key = (Project UUID, Parent UUID, Code, CSV Payor).

Linear-side dedup: if existing_customer_tickets.csv exists (produced by
check_existing_tickets.py), rows whose (Parent Issue UUID, Code) is
already in that file are skipped. This catches re-runs after a partial
crash or accidental re-onboarding of an already-onboarded customer.

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
    """(Project UUID, Code) → {"uuid": Parent Issue UUID,
                                "state_id": parent's State UUID or ""}.

    Merges two sources, in order of preference:
      1. parents_created.csv  — parents this run just created
      2. existing_parents.csv — parents already in Linear (auto-pulled
         by check_existing_tickets.py)

    Either source's UUID is fine; we keep whichever we see first.
    `state_id` may be empty string for older tracker files that pre-date
    the State UUID column — the caller falls back to the team default.
    """
    out = {}
    for fname in ("parents_created.csv", "existing_parents.csv"):
        path = os.path.join(cdir, fname)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            puuid = (r.get("Project UUID") or "").strip()
            code  = (r.get("Code") or "").strip()
            iuuid = (r.get("Issue UUID") or "").strip()
            state = (r.get("State UUID") or "").strip()
            if puuid and code and iuuid:
                out.setdefault((puuid, code),
                               {"uuid": iuuid, "state_id": state})
    return out


def load_existing_customer_tickets(cdir):
    """{(Parent Issue UUID, Code) → Issue UUID} for customer tickets that
    already exist in Linear (the customer's Qual Criteria project).
    Empty dict if check_existing_tickets.py wasn't run yet."""
    path = os.path.join(cdir, "existing_customer_tickets.csv")
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            parent = (r.get("Parent Issue UUID") or "").strip()
            code   = (r.get("Code") or "").strip()
            iuuid  = (r.get("Issue UUID") or "").strip()
            if parent and code:
                out[(parent, code)] = iuuid
    return out


def make_title(code, desc):
    """Convention: '<HCPCS> - <Description>'. Falls back to just the
    code when no description is available."""
    code = (code or "").strip()
    desc = (desc or "").strip()
    if code and desc:
        return f"{code} - {desc}"
    return code or desc


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
    existing_cust = load_existing_customer_tickets(cdir)
    state_id, team_uuid = state_uuid_for(team_full)
    cust_proj = cfg["customer_project_id"]

    print(f"loaded {len(parents)} parents, {len(matches)} payor matches, "
          f"{len(labels)} team labels, {len(existing_cust)} existing "
          f"customer tickets", file=sys.stderr)
    if not existing_cust:
        print(f"⚠ no existing_customer_tickets.csv found — run "
              f"check_existing_tickets.py first to dedup against tickets "
              f"already in the customer's Qual Criteria project",
              file=sys.stderr)

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

    created = skipped = skipped_existing = failed = 0
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
        parent_info = parents.get((proj, code))
        if not parent_info:
            miss_parent += 1
            print(f"  MISS PARENT [{i}] {m['matched']}/{code}", file=sys.stderr)
            continue
        parent_uuid  = parent_info["uuid"]
        # Inherit the parent's workflow state. Older tracker files
        # don't have State UUID — fall back to the team's "Not Started"
        # so we never send a malformed mutation.
        parent_state = parent_info["state_id"] or state_id
        key = (proj, parent_uuid, code, payor)
        if key in done:
            skipped += 1
            continue
        # Linear-side dedup: skip if a customer ticket for this parent +
        # code already exists in the customer's Qual Criteria project.
        if (parent_uuid, code) in existing_cust:
            skipped_existing += 1
            continue

        payor_label = labels.get(m["matched"].lower(), "")
        sl_label    = labels.get(sl.lower(), "") if sl else ""
        if not payor_label:
            miss_label += 1
            print(f"  MISS LABEL [{i}] {m['matched']!r}", file=sys.stderr)
            continue

        title = make_title(code, titles.get(code, ""))
        payload = {
            "title":     title,
            "teamId":    team_uuid,
            "projectId": cust_proj,
            "parentId":  parent_uuid,
            "labelIds":  [x for x in (payor_label, sl_label) if x],
            "stateId":   parent_state,
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
                "Parent Issue UUID": parent_uuid,
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
    print(f"\nDone. created={created} skipped={skipped} "
          f"skipped_existing={skipped_existing} failed={failed} "
          f"miss_parent={miss_parent} miss_label={miss_label} "
          f"elapsed={el/60:.1f}m", file=sys.stderr)


if __name__ == "__main__":
    main()
