#!/usr/bin/env python3
"""Attach a Linear Customer Need linking each parent ticket to the
customer's Linear Customer record.

Reads:
  ~/Desktop/Customers/<name>/customer_config.json   (customer_id)
  ~/Desktop/Customers/<name>/parents_created.csv
  ~/Desktop/Customers/<name>/existing_parents.csv   (optional)

Writes:
  ~/Desktop/Customers/<name>/customer_needs_created.csv  (resumable)

⚠ Linear does NOT dedupe Customer Needs by (customerId, issueId). The
script's tracker prevents duplicates within its history, but if a parent
already has a Need attached for this customer outside this script,
re-running will create a duplicate. Manually trim the rows you want to
re-process from the tracker first.

Usage:
  python3 create_parent_customer_needs.py "Comfort Medical"
  python3 create_parent_customer_needs.py "Comfort Medical" --sleep 1.5
  python3 create_parent_customer_needs.py "Comfort Medical" --start 0 --limit 1000
"""
import argparse
import csv
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import customer_dir, load_config, get_token, gql_with_retry

MUTATION = """
mutation CustomerNeedCreate($input: CustomerNeedCreateInput!) {
  customerNeedCreate(input: $input) {
    success
    need { id }
  }
}"""


def create_need(customer_id, issue_uuid, token):
    data = gql_with_retry(MUTATION,
                          {"input": {"customerId": customer_id,
                                     "issueId": issue_uuid}}, token)
    ic = data["customerNeedCreate"]
    if not ic["success"]:
        raise RuntimeError(f"customerNeedCreate.success=false: {ic}")
    return ic["need"]["id"]


def load_parents(cdir):
    """List of {uuid, identifier, project, code}, deduped by uuid, in order."""
    out, seen = [], set()
    for fname in ("parents_created.csv", "existing_parents.csv"):
        path = os.path.join(cdir, fname)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            uuid = r.get("Issue UUID", "").strip()
            if not uuid or uuid in seen:
                continue
            seen.add(uuid)
            out.append({
                "uuid": uuid,
                "identifier": r.get("Issue ID", ""),
                "project": r.get("Matched Project", ""),
                "code": r.get("Code", ""),
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=1.5)
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    cfg = load_config(args.customer_name)
    customer_id = cfg["customer_id"]

    parents = load_parents(cdir)
    print(f"loaded {len(parents)} parent tickets", file=sys.stderr)

    tracker = os.path.join(cdir, "customer_needs_created.csv")
    done = set()
    if os.path.exists(tracker):
        for r in csv.DictReader(open(tracker)):
            done.add(r["Parent Issue UUID"])
        print(f"Resume: {len(done)} needs in tracker", file=sys.stderr)

    end = len(parents) if args.limit is None else min(len(parents),
                                                       args.start + args.limit)
    window = parents[args.start:end]
    print(f"Window: {args.start}..{end-1} ({len(window)} parents)",
          file=sys.stderr)

    token = get_token()
    new = not os.path.exists(tracker)
    tf = open(tracker, "a", newline="")
    fields = ["Parent Issue UUID", "Parent Issue ID", "Matched Project",
              "Code", "Need ID"]
    w = csv.DictWriter(tf, fieldnames=fields)
    if new:
        w.writeheader(); tf.flush()

    created = skipped = failed = 0
    t0 = time.time()
    for i, p in enumerate(window, 1):
        if p["uuid"] in done:
            skipped += 1
            continue
        try:
            need_id = create_need(customer_id, p["uuid"], token)
            w.writerow({
                "Parent Issue UUID": p["uuid"],
                "Parent Issue ID": p["identifier"],
                "Matched Project": p["project"],
                "Code": p["code"],
                "Need ID": need_id,
            })
            tf.flush(); os.fsync(tf.fileno())
            done.add(p["uuid"])
            created += 1
            if created % 50 == 0:
                el = time.time() - t0
                rate = created / el * 60
                eta = (len(window) - i) / max(rate / 60, 0.01) / 60
                print(f"  [{i}/{len(window)}] need={need_id} on "
                      f"{p['identifier']} (rate={rate:.0f}/min, ETA {eta:.1f}m)",
                      file=sys.stderr)
            time.sleep(args.sleep)
        except Exception as e:
            failed += 1
            print(f"  FAIL [{i}] {p['identifier']} ({p['project']} "
                  f"{p['code']}): {e}", file=sys.stderr)
            time.sleep(2)

    tf.close()
    el = time.time() - t0
    print(f"\nDone. created={created} skipped={skipped} failed={failed} "
          f"elapsed={el/60:.1f}m", file=sys.stderr)


if __name__ == "__main__":
    main()
