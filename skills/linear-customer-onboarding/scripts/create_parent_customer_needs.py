#!/usr/bin/env python3
"""Attach a Linear Customer Need linking each in-scope parent ticket to
the customer's Linear Customer record.

Scope rule (important):
  A parent is "in scope" for this customer if the customer's input.csv
  + payor_matches.csv produce a (Project UUID, Code) row for it. That
  catches two cases:

  1. Parents this run just created — every row in parents_created.csv
     is in scope by construction (we wouldn't have created it if the
     customer's input didn't ask for it).
  2. Pre-existing parents that ALSO match the customer's input — e.g.,
     another customer was onboarded last month with the same payor +
     code, so the parent already exists. The current customer also
     cares about it; they should show up on the Needs list too.

  Pre-existing parents that the current customer's input does NOT
  reference — even if they sit in the same Insurance project — are out
  of scope and do not get a Need.

Reads:
  ~/Desktop/Customers/<name>/customer_config.json   (customer_id)
  ~/Desktop/Customers/<name>/input.csv              (CSV Payor + Code)
  ~/Desktop/Customers/<name>/payor_matches.csv      (Payor → Project UUID)
  ~/Desktop/Customers/<name>/parents_created.csv
  ~/Desktop/Customers/<name>/existing_parents.csv   (optional;
       intersected with the (Project, Code) scope above)

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


def load_customer_scope(cdir):
    """Set of (Project UUID, Code) that this customer's input.csv +
    payor_matches.csv cares about. Used to filter existing_parents.csv
    so we only attach Needs to pre-existing parents the customer
    actually asked for."""
    pm_path = os.path.join(cdir, "payor_matches.csv")
    in_path = os.path.join(cdir, "input.csv")
    if not os.path.exists(pm_path) or not os.path.exists(in_path):
        # Without these we can't compute scope. Fall back to "no
        # pre-existing parents in scope" — only parents_created.csv
        # will be processed, which is the safe choice.
        return None
    payor_to_proj = {}
    for r in csv.DictReader(open(pm_path)):
        p = (r.get("CSV Payor") or "").strip()
        u = (r.get("Project UUID") or "").strip()
        if p and u:
            payor_to_proj[p] = u
    scope = set()
    for r in csv.DictReader(open(in_path)):
        payor = (r.get("CSV Payor") or "").strip()
        code  = (r.get("Code") or "").strip()
        proj  = payor_to_proj.get(payor)
        if proj and code:
            scope.add((proj, code))
    return scope


def load_parents(cdir):
    """List of {uuid, identifier, project, code, source}, deduped by
    uuid, in order. Includes:

      - Every parent in parents_created.csv (this run created them, so
        they're definitely in scope).
      - Pre-existing parents from existing_parents.csv whose (Project
        UUID, Code) appears in the customer's input scope.

    Pre-existing parents that aren't in the customer's input — even if
    they live in one of the same Insurance projects — are filtered out.
    """
    out, seen = [], set()
    scope = load_customer_scope(cdir)

    # Parents we just created — always in scope.
    created_path = os.path.join(cdir, "parents_created.csv")
    if os.path.exists(created_path):
        for r in csv.DictReader(open(created_path)):
            uuid = (r.get("Issue UUID") or "").strip()
            if not uuid or uuid in seen:
                continue
            seen.add(uuid)
            out.append({
                "uuid":       uuid,
                "identifier": r.get("Issue ID", ""),
                "project":    r.get("Matched Project", ""),
                "code":       r.get("Code", ""),
                "source":     "parents_created",
            })

    # Pre-existing parents — only those in this customer's scope.
    existing_path = os.path.join(cdir, "existing_parents.csv")
    if os.path.exists(existing_path) and scope is not None:
        in_scope = 0
        out_scope = 0
        for r in csv.DictReader(open(existing_path)):
            uuid = (r.get("Issue UUID") or "").strip()
            puuid = (r.get("Project UUID") or "").strip()
            code  = (r.get("Code") or "").strip()
            if not uuid or uuid in seen:
                continue
            if (puuid, code) not in scope:
                out_scope += 1
                continue
            seen.add(uuid)
            in_scope += 1
            out.append({
                "uuid":       uuid,
                "identifier": r.get("Issue ID", ""),
                "project":    r.get("Matched Project", ""),
                "code":       code,
                "source":     "existing_in_scope",
            })
        print(f"existing_parents.csv: {in_scope} in scope (will get "
              f"Needs), {out_scope} out of scope (skipped)",
              file=sys.stderr)
    elif os.path.exists(existing_path) and scope is None:
        print(f"⚠ existing_parents.csv present but input.csv / "
              f"payor_matches.csv missing — cannot compute scope, so "
              f"pre-existing parents are SKIPPED to be safe. Provide "
              f"both files to include shared parents.", file=sys.stderr)

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
    by_src = {}
    for p in parents:
        by_src[p["source"]] = by_src.get(p["source"], 0) + 1
    print(f"loaded {len(parents)} in-scope parent tickets " +
          ("(" + ", ".join(f"{v} {k}" for k, v in by_src.items()) + ")"
           if by_src else ""), file=sys.stderr)

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
