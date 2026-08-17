#!/usr/bin/env python3
"""
refresh_insurance_issues.py

Exports all issues from the Insurance initiative in Linear to:
  ~/Claude/Projects/Linear Master Data/
    insurance_initiative_issues_<timestamp>.csv   ← timestamped snapshot
    insurance_initiative_issues_latest.csv         ← always the freshest

Also updates insurance_initiative_export_metadata.json.

Usage:
  python3 refresh_insurance_issues.py

Auth:
  Reads token from ~/Claude/Projects/Credentials/linear_tokens.json
"""

import requests, json, csv, datetime, time
from pathlib import Path

TOKEN_FILE  = Path.home() / "Claude/Projects/Credentials/linear_tokens.json"
OUT_DIR     = Path.home() / "Claude/Projects/Linear Master Data"
API         = "https://api.linear.app/graphql"
INITIATIVE_ID = "3f3a1212-8cb2-4afe-bcd5-4c8b8f0104de"

token   = json.loads(TOKEN_FILE.read_text())["access_token"]
headers = {"Authorization": token, "Content-Type": "application/json"}

ISSUES_Q = """
query ($cursor: String) {
  issues(
    first: 250,
    after: $cursor,
    filter: {
      project: { initiatives: { id: { eq: "3f3a1212-8cb2-4afe-bcd5-4c8b8f0104de" } } }
    }
  ) {
    nodes {
      identifier
      title
      state { name type }
      project { name }
      team { name }
      estimate
      priority
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

def main():
    issues = []
    cursor = None
    page   = 0

    print("Fetching insurance initiative issues…", flush=True)
    while True:
        r = requests.post(API, headers=headers,
                          json={"query": ISSUES_Q, "variables": {"cursor": cursor}},
                          timeout=30)
        r.raise_for_status()
        d = r.json()
        if "errors" in d:
            raise RuntimeError(f"GraphQL error: {d['errors']}")

        nodes = d["data"]["issues"]["nodes"]
        issues.extend(nodes)
        page += 1
        print(f"  page {page}: +{len(nodes)} (total {len(issues)})", flush=True)

        pi = d["data"]["issues"]["pageInfo"]
        if not pi["hasNextPage"]:
            break
        cursor = pi["endCursor"]
        time.sleep(0.15)

    now      = datetime.datetime.now(datetime.timezone.utc)
    ts_str   = now.strftime("%Y-%m-%d_%H%M")
    ts_fname = f"insurance_initiative_issues_{ts_str}.csv"

    fieldnames = ["Identifier", "Title", "State", "State Type", "Project", "Team", "Estimate", "Priority"]
    for fname in [ts_fname, "insurance_initiative_issues_latest.csv"]:
        with open(OUT_DIR / fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for iss in issues:
                w.writerow({
                    "Identifier": iss.get("identifier", ""),
                    "Title":      iss.get("title", ""),
                    "State":      (iss.get("state") or {}).get("name", ""),
                    "State Type": (iss.get("state") or {}).get("type", ""),
                    "Project":    (iss.get("project") or {}).get("name", ""),
                    "Team":       (iss.get("team") or {}).get("name", ""),
                    "Estimate":   iss.get("estimate", ""),
                    "Priority":   iss.get("priority", ""),
                })

    meta = {
        "last_export":   now.isoformat(),
        "initiative":    "Insurance",
        "initiative_id": INITIATIVE_ID,
        "n_issues":      len(issues),
        "file":          ts_fname,
    }
    (OUT_DIR / "insurance_initiative_export_metadata.json").write_text(
        json.dumps(meta, indent=2)
    )

    print(f"\nDone: {len(issues)} issues → {ts_fname}")

if __name__ == "__main__":
    main()
