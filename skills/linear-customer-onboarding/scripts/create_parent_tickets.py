#!/usr/bin/env python3
"""Create parent tickets in Linear from parent_plan.csv.

Reads:   ~/Desktop/Customers/<name>/parent_plan.csv
Writes:  ~/Desktop/Customers/<name>/parents_created.csv  (resumable tracker)

Resumable. Re-running skips rows already in the tracker (keyed on
(Project UUID, Code)). Handles Linear's 2,500 req/hr cap.

Usage:
  python3 create_parent_tickets.py "Comfort Medical"
  python3 create_parent_tickets.py "Comfort Medical" --sleep 1.5
  python3 create_parent_tickets.py "Comfort Medical" --start 1000 --limit 500
"""
import argparse
import csv
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import customer_dir, get_token, gql_with_retry

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=1.5,
                    help="Seconds between successful creates. Default 1.5 = "
                         "~40/min (sustainable under Linear's 2500/hr cap).")
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    plan_path = os.path.join(cdir, "parent_plan.csv")
    tracker   = os.path.join(cdir, "parents_created.csv")
    if not os.path.exists(plan_path):
        sys.exit(f"missing {plan_path} — run build_parent_plan.py first")

    token = get_token()

    # Resume: load done keys
    done = set()
    if os.path.exists(tracker):
        for r in csv.DictReader(open(tracker)):
            done.add((r["Project UUID"], r["Code"]))
        print(f"Resume: {len(done)} parents in tracker", file=sys.stderr)

    rows = list(csv.DictReader(open(plan_path)))
    end = len(rows) if args.limit is None else min(len(rows),
                                                   args.start + args.limit)
    window = rows[args.start:end]
    print(f"Window: {args.start}..{end-1} ({len(window)} of {len(rows)})",
          file=sys.stderr)

    new = not os.path.exists(tracker)
    tf = open(tracker, "a", newline="")
    fields = ["Matched Project", "Code", "Title", "Project UUID",
              "Issue UUID", "Issue ID", "URL", "Priority", "Total Volume",
              "State UUID"]
    w = csv.DictWriter(tf, fieldnames=fields)
    if new:
        w.writeheader(); tf.flush()

    created = skipped = failed = 0
    t0 = time.time()
    for i, r in enumerate(window, 1):
        key = (r["Project UUID"], r["Code"])
        if key in done:
            skipped += 1
            continue
        payload = {
            "title":     r["Title"],
            "teamId":    r["Team UUID"],
            "projectId": r["Project UUID"],
            "labelIds":  [x for x in r["Payor Label UUIDs"].split("|") if x],
            "stateId":   r["State UUID"],
            "priority":  int(r["Priority"]),
            "estimate":  int(r["Estimate"]),
        }
        try:
            uuid, ident, url = create_issue(payload, token)
            w.writerow({
                "Matched Project": r["Matched Project"],
                "Code": r["Code"],
                "Title": r["Title"],
                "Project UUID": r["Project UUID"],
                "Issue UUID": uuid,
                "Issue ID": ident,
                "URL": url,
                "Priority": r["Priority"],
                "Total Volume": r["Total Volume"],
                "State UUID": r["State UUID"],
            })
            tf.flush(); os.fsync(tf.fileno())
            done.add(key)
            created += 1
            if created % 25 == 0:
                el = time.time() - t0
                rate = created / el * 60
                eta = (len(window) - i) / max(rate / 60, 0.01) / 60
                print(f"  [{i}/{len(window)}] {ident} created "
                      f"(rate={rate:.0f}/min, ETA {eta:.1f}m)",
                      file=sys.stderr)
            time.sleep(args.sleep)
        except Exception as e:
            failed += 1
            print(f"  FAIL [{i}] {r['Matched Project']} {r['Code']}: {e}",
                  file=sys.stderr)
            time.sleep(2)

    tf.close()
    el = time.time() - t0
    print(f"\nDone. created={created} skipped={skipped} failed={failed} "
          f"elapsed={el/60:.1f}m", file=sys.stderr)


if __name__ == "__main__":
    main()
