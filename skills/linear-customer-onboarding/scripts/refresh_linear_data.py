#!/usr/bin/env python3
"""Refresh the master Linear data into ~/Desktop/Linear Master Data/.

Pulls (paginated):
  - all teams (writes teams.csv)
  - all DME Criteria team labels (dme_team_labels.csv)
  - all Infusion Criteria team labels (infusion_team_labels.csv)
  - all workspace projects (insurance_projects.csv — caller filters
    later to insurance ones by name)
  - all workflow states for those teams (workflow_states.csv)

Writes refresh_metadata.json with last-pulled timestamps.

Usage:
  python3 refresh_linear_data.py
  python3 refresh_linear_data.py --teams "DME Criteria,Infusion Criteria"
"""
import argparse
import csv
import datetime
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import (gql_with_retry, get_token, MASTER_DIR)

DEFAULT_TEAMS = ["DME Criteria", "Infusion Criteria"]


def fetch_teams(token):
    Q = "query { teams(first: 250) { nodes { id name key } } }"
    data = gql_with_retry(Q, {}, token)
    return data["teams"]["nodes"]


def fetch_team_labels(team_id, token):
    Q = """
    query Labels($teamId: String!, $cursor: String) {
      team(id: $teamId) {
        labels(first: 250, after: $cursor) {
          nodes { id name }
          pageInfo { hasNextPage endCursor }
        }
      }
    }"""
    out, cursor = [], None
    while True:
        data = gql_with_retry(Q, {"teamId": team_id, "cursor": cursor}, token)
        page = data["team"]["labels"]
        out.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return out


def fetch_projects(token):
    Q = """
    query Projects($cursor: String) {
      projects(first: 250, after: $cursor) {
        nodes { id name }
        pageInfo { hasNextPage endCursor }
      }
    }"""
    out, cursor = [], None
    while True:
        data = gql_with_retry(Q, {"cursor": cursor}, token)
        page = data["projects"]
        out.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return out


def fetch_workflow_states(team_id, token):
    Q = """
    query States($teamId: String!) {
      team(id: $teamId) {
        states(first: 100) {
          nodes { id name type }
        }
      }
    }"""
    data = gql_with_retry(Q, {"teamId": team_id}, token)
    return data["team"]["states"]["nodes"]


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teams", default=",".join(DEFAULT_TEAMS),
                    help="Comma-sep team names to pull labels+states for")
    args = ap.parse_args()
    target_teams = [t.strip() for t in args.teams.split(",") if t.strip()]

    os.makedirs(MASTER_DIR, exist_ok=True)
    token = get_token()

    print("fetching teams…", file=sys.stderr)
    teams = fetch_teams(token)
    write_csv(os.path.join(MASTER_DIR, "teams.csv"),
              [{"Name": t["name"], "Key": t["key"], "UUID": t["id"]} for t in teams],
              ["Name", "Key", "UUID"])

    name_to_team = {t["name"]: t for t in teams}

    states_rows = []
    label_files = {"DME Criteria": "dme_team_labels.csv",
                   "Infusion Criteria": "infusion_team_labels.csv"}

    for tname in target_teams:
        if tname not in name_to_team:
            print(f"  WARN: team {tname!r} not found; skipping",
                  file=sys.stderr)
            continue
        t = name_to_team[tname]
        print(f"fetching labels for {tname}…", file=sys.stderr)
        labels = fetch_team_labels(t["id"], token)
        # Pick a sensible filename
        slug = label_files.get(tname,
                               tname.lower().replace(" ", "_") + "_labels.csv")
        path = os.path.join(MASTER_DIR, slug)
        write_csv(path,
                  [{"Name": L["name"], "UUID": L["id"]} for L in labels],
                  ["Name", "UUID"])
        print(f"  wrote {len(labels)} labels → {path}", file=sys.stderr)

        print(f"fetching workflow states for {tname}…", file=sys.stderr)
        for s in fetch_workflow_states(t["id"], token):
            states_rows.append({"Team": tname, "TeamUUID": t["id"],
                                "Name": s["name"], "Type": s["type"],
                                "UUID": s["id"]})

    write_csv(os.path.join(MASTER_DIR, "workflow_states.csv"),
              states_rows, ["Team", "TeamUUID", "Name", "Type", "UUID"])

    print("fetching projects…", file=sys.stderr)
    projects = fetch_projects(token)
    write_csv(os.path.join(MASTER_DIR, "insurance_projects.csv"),
              [{"Name": p["name"], "UUID": p["id"]} for p in projects],
              ["Name", "UUID"])
    print(f"  wrote {len(projects)} projects", file=sys.stderr)

    meta = {
        "last_refresh": datetime.datetime.utcnow().isoformat() + "Z",
        "teams_pulled": target_teams,
        "n_teams": len(teams),
        "n_projects": len(projects),
        "n_workflow_states": len(states_rows),
    }
    with open(os.path.join(MASTER_DIR, "refresh_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\ndone. metadata: {meta}", file=sys.stderr)


if __name__ == "__main__":
    main()
