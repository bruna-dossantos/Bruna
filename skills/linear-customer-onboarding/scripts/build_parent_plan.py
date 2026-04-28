#!/usr/bin/env python3
"""Build the per-customer parent ticket plan.

Reads:
  ~/Desktop/Customers/<name>/input.csv         (Payor, Code, Volume, [Service Line])
  ~/Desktop/Customers/<name>/payor_matches.csv (Payor → Project UUID)
  ~/Desktop/Customers/<name>/code_titles.csv   (Code → Title) — optional
  ~/Desktop/Customers/<name>/customer_config.json
  ~/Desktop/Linear Master Data/<team>_team_labels.csv
  ~/Desktop/Linear Master Data/workflow_states.csv

Writes:
  ~/Desktop/Customers/<name>/parent_plan.csv

Fields written:
  Matched Project, Project UUID, Code, Title, Payor Label UUIDs (pipe),
  Service Line, Service Line UUID, Total Volume, Priority, State UUID,
  Team UUID, Estimate

Priority is assigned by volume quartile across the whole dataset:
  >= Q3 -> 1 (Urgent), >= Q2 -> 2 (High), >= Q1 -> 3 (Normal), else 4 (Low)

Where Q1/Q2/Q3 are the 25th/50th/75th percentiles of Total Volume.

Usage:
  python3 build_parent_plan.py "Comfort Medical"
"""
import argparse
import csv
import json
import os
import statistics
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import (customer_dir, load_config, team_labels_path,
                  workflow_states_path, PARENT_ESTIMATE)


def load_team_labels(team):
    """name (lowercased) → UUID"""
    out = {}
    with open(team_labels_path(team)) as f:
        for r in csv.DictReader(f):
            out[r["Name"].strip().lower()] = r["UUID"].strip()
    return out


def load_payor_matches(cdir):
    """CSV Payor → (Matched Project, Project UUID)"""
    path = os.path.join(cdir, "payor_matches.csv")
    if not os.path.exists(path):
        sys.exit(f"missing {path} — run match_payors.py first")
    out = {}
    for r in csv.DictReader(open(path)):
        out[r["CSV Payor"].strip()] = {
            "matched": r["Matched Project"].strip(),
            "uuid": r["Project UUID"].strip(),
        }
    return out


def load_titles(cdir):
    path = os.path.join(cdir, "code_titles.csv")
    if not os.path.exists(path):
        return {}
    return {r["Code"].strip(): r["Title"].strip()
            for r in csv.DictReader(open(path))}


def state_uuid_for(team_name, state_name="Not Started"):
    with open(workflow_states_path()) as f:
        for r in csv.DictReader(f):
            if r["Team"] == team_name and r["Name"] == state_name:
                return r["UUID"], r["TeamUUID"]
    sys.exit(f"could not find state {state_name!r} for team {team_name!r} — "
             f"refresh master data")


def quartile_priority(vol, q1, q2, q3):
    if vol >= q3: return 1
    if vol >= q2: return 2
    if vol >= q1: return 3
    return 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    cfg  = load_config(args.customer_name)
    team = cfg["team"]
    team_full_name = {"dme": "DME Criteria",
                      "infusion": "Infusion Criteria"}.get(team)
    if not team_full_name:
        sys.exit(f"unknown team in config: {team!r}")

    team_labels = load_team_labels(team)
    payor_match = load_payor_matches(cdir)
    titles      = load_titles(cdir)
    state_id, team_uuid = state_uuid_for(team_full_name)

    # 1. Aggregate (Project UUID, Code) -> volume + raw rows
    agg = {}
    in_path = os.path.join(cdir, "input.csv")
    with open(in_path) as f:
        for r in csv.DictReader(f):
            payor = r.get("CSV Payor", "").strip()
            code  = r.get("Code", "").strip()
            try:
                vol = int(float(r.get("Volume", "0") or "0"))
            except ValueError:
                vol = 0
            sl    = r.get("Service Line", "").strip()
            pm = payor_match.get(payor)
            if not pm or not pm["uuid"]:
                continue  # unmatched payor — skip silently; preview script
                          # will surface this
            key = (pm["uuid"], code)
            if key not in agg:
                agg[key] = {
                    "matched": pm["matched"],
                    "project_uuid": pm["uuid"],
                    "code": code,
                    "service_line": sl,
                    "volume": 0,
                    "payors": set(),
                }
            agg[key]["volume"] += vol
            if sl and not agg[key]["service_line"]:
                agg[key]["service_line"] = sl
            agg[key]["payors"].add(payor)

    rows = list(agg.values())
    print(f"aggregated to {len(rows)} (project × code) parents",
          file=sys.stderr)

    # 2. Compute quartile thresholds
    vols = sorted(r["volume"] for r in rows if r["volume"] > 0)
    if len(vols) >= 4:
        q1 = statistics.quantiles(vols, n=4)[0]
        q2 = statistics.median(vols)
        q3 = statistics.quantiles(vols, n=4)[2]
    else:
        q1 = q2 = q3 = 0
    print(f"volume quartiles: Q1={q1:.0f}  Q2={q2:.0f}  Q3={q3:.0f}",
          file=sys.stderr)

    # 3. Resolve labels + emit
    missing_payor_labels = set()
    missing_sl_labels    = set()
    out_rows = []
    for r in rows:
        proj_name = r["matched"]
        payor_uuid = team_labels.get(proj_name.lower(), "")
        if not payor_uuid:
            missing_payor_labels.add(proj_name)
        sl_uuid = ""
        if r["service_line"]:
            sl_uuid = team_labels.get(r["service_line"].lower(), "")
            if not sl_uuid:
                missing_sl_labels.add(r["service_line"])
        title = titles.get(r["code"]) or r["code"]
        out_rows.append({
            "Matched Project": proj_name,
            "Project UUID":    r["project_uuid"],
            "Code":            r["code"],
            "Title":           title,
            "Payor Label UUIDs": "|".join(x for x in (payor_uuid, sl_uuid) if x),
            "Service Line":    r["service_line"],
            "Service Line UUID": sl_uuid,
            "Total Volume":    r["volume"],
            "Priority":        quartile_priority(r["volume"], q1, q2, q3),
            "State UUID":      state_id,
            "Team UUID":       team_uuid,
            "Estimate":        PARENT_ESTIMATE,
        })

    if missing_payor_labels or missing_sl_labels:
        print("\n⚠ MISSING LABELS — refusing to write plan.\n", file=sys.stderr)
        if missing_payor_labels:
            print("Payor labels missing from team labels CSV:", file=sys.stderr)
            for n in sorted(missing_payor_labels):
                print(f"  - {n}", file=sys.stderr)
        if missing_sl_labels:
            print("Service line labels missing:", file=sys.stderr)
            for n in sorted(missing_sl_labels):
                print(f"  - {n}", file=sys.stderr)
        print(f"\nFix with:  python3 create_team_label.py "
              f"\"{args.customer_name}\" --names \"<name1>\" \"<name2>\" …",
              file=sys.stderr)
        sys.exit(2)

    out_path = os.path.join(cdir, "parent_plan.csv")
    fields = ["Matched Project", "Project UUID", "Code", "Title",
              "Payor Label UUIDs", "Service Line", "Service Line UUID",
              "Total Volume", "Priority", "State UUID", "Team UUID",
              "Estimate"]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(out_rows, key=lambda x: (x["Priority"], -x["Total Volume"])))

    # Summary
    by_pri = {}
    for r in out_rows:
        by_pri[r["Priority"]] = by_pri.get(r["Priority"], 0) + 1
    print(f"\nwrote {out_path}", file=sys.stderr)
    print(f"  total parents: {len(out_rows)}", file=sys.stderr)
    for p in sorted(by_pri):
        label = {1:"Urgent",2:"High",3:"Normal",4:"Low"}[p]
        print(f"  P{p} ({label}): {by_pri[p]}", file=sys.stderr)


if __name__ == "__main__":
    main()
