#!/usr/bin/env python3
"""Fuzzy-match a customer's CSV Payor names to Linear Insurance projects.

Reads:
  ~/Desktop/Customers/<name>/input.csv      (CSV Payor column)
  ~/Desktop/Linear Master Data/insurance_projects.csv

Writes:
  ~/Desktop/Customers/<name>/payor_matches.csv

Fields written:
  CSV Payor, Matched Project, Project UUID, Confidence, N Rows

Confidence is difflib.SequenceMatcher.ratio() (0..1). Rows with confidence
< 0.85 are flagged for human review by the SKILL.md orchestrator.

Usage:
  python3 match_payors.py "Comfort Medical"
  python3 match_payors.py "Comfort Medical" --threshold 0.6
"""
import argparse
import csv
import difflib
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import customer_dir, insurance_projects_path


# Common normalizations to strip noise before fuzzy match
def norm(s):
    s = (s or "").lower().strip()
    for prefix in ("dnu-", "dnu ", "old ", "legacy "):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def load_projects():
    rows = []
    with open(insurance_projects_path()) as f:
        for r in csv.DictReader(f):
            rows.append({"name": r["Name"], "uuid": r["UUID"],
                         "norm": norm(r["Name"])})
    return rows


def match_one(payor, projects):
    """Return (best_project_dict, score) or (None, 0)."""
    p_norm = norm(payor)
    if not p_norm:
        return None, 0.0
    # Exact normalized match → 1.0
    for proj in projects:
        if proj["norm"] == p_norm:
            return proj, 1.0
    # Fuzzy ratio
    best, best_score = None, 0.0
    for proj in projects:
        s = difflib.SequenceMatcher(None, p_norm, proj["norm"]).ratio()
        if s > best_score:
            best, best_score = proj, s
    return best, best_score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name", help="folder name under ~/Desktop/Customers/")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="minimum confidence to record a match (else blank)")
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    in_path = os.path.join(cdir, "input.csv")
    if not os.path.exists(in_path):
        sys.exit(f"missing {in_path}")
    out_path = os.path.join(cdir, "payor_matches.csv")

    # Count distinct payors and their row counts
    counts = {}
    with open(in_path) as f:
        for r in csv.DictReader(f):
            p = r.get("CSV Payor", "").strip()
            if not p:
                continue
            counts[p] = counts.get(p, 0) + 1
    print(f"loaded {sum(counts.values())} rows, {len(counts)} unique payors",
          file=sys.stderr)

    projects = load_projects()
    print(f"loaded {len(projects)} insurance projects", file=sys.stderr)

    rows = []
    low_conf = 0
    no_match = 0
    for payor in sorted(counts):
        proj, score = match_one(payor, projects)
        if score < args.threshold:
            no_match += 1
            rows.append({"CSV Payor": payor,
                         "Matched Project": "",
                         "Project UUID": "",
                         "Confidence": f"{score:.3f}",
                         "N Rows": counts[payor]})
            continue
        if score < 0.85:
            low_conf += 1
        rows.append({"CSV Payor": payor,
                     "Matched Project": proj["name"],
                     "Project UUID": proj["uuid"],
                     "Confidence": f"{score:.3f}",
                     "N Rows": counts[payor]})

    fields = ["CSV Payor", "Matched Project", "Project UUID",
              "Confidence", "N Rows"]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {out_path}", file=sys.stderr)
    print(f"  matched (confidence >= 0.85): {len(rows)-low_conf-no_match}",
          file=sys.stderr)
    print(f"  needs review (conf 0.5..0.85): {low_conf}", file=sys.stderr)
    print(f"  unmatched (conf < {args.threshold}): {no_match}",
          file=sys.stderr)
    if low_conf or no_match:
        print(f"\n  → review {out_path} and fix the Matched Project / "
              f"Project UUID columns before continuing.", file=sys.stderr)


if __name__ == "__main__":
    main()
