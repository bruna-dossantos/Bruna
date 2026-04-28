#!/usr/bin/env python3
"""Pre-flight: query Linear for existing tickets so we don't create duplicates.

Run this AFTER match_payors.py (so we know which Insurance projects to
query) and BEFORE build_parent_plan.py (so the plan can skip rows
already in Linear).

Why this script exists:
  Without this, build_parent_plan.py only dedupes within the input CSV
  — it has no idea which (project, code) parents already exist in
  Linear. That can mean creating thousands of duplicates if you re-run
  on a customer who's already been partially onboarded, or if another
  customer's onboarding already created the parent for the same
  insurance project + HCPCS code.

What it queries:
  - Every Insurance project listed in payor_matches.csv → all top-level
    issues, parsed for leading HCPCS code in their titles.
  - The customer's Qual Criteria project → every customer ticket with
    its parentId, parsed for leading code.

Reads:
  ~/Desktop/Customers/<name>/payor_matches.csv
  ~/Desktop/Customers/<name>/customer_config.json

Writes:
  ~/Desktop/Customers/<name>/existing_parents.csv
    columns: Project UUID, Matched Project, Code, Title,
             Issue UUID, Issue ID, URL
  ~/Desktop/Customers/<name>/existing_customer_tickets.csv
    columns: Parent Issue UUID, Code, Title, Issue UUID, Issue ID,
             URL, Labels

Both files use code parsed from issue titles (the convention is
"<HCPCS> - <Description>", e.g. "A4351 - Indwelling Catheter"). Issues
with titles that don't start with a code-shaped token are skipped — they
won't collide with anything we plan to create.

Usage:
  python3 check_existing_tickets.py "Comfort Medical"
  python3 check_existing_tickets.py "Comfort Medical" --sleep 1.0
"""
import argparse
import csv
import os
import re
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import customer_dir, load_config, get_token, gql_with_retry


# Recognized code shapes:
#   HCPCS Level II:  letter + 4 digits           (A4351, J9035, E0601)
#   HCPCS Level II:  letter + 4 digits + suffix  (A4351NU)  — accepted
#   CPT (Level I):   5 digits                    (99214)
# The regex matches the leading token; everything after the first " - "
# (or end of string) is the human description and we don't care about it.
CODE_RE = re.compile(
    r"^\s*([A-Za-z]\d{4,5}[A-Za-z0-9]*|\d{5})(?:\s*[-:–—]\s*|\s*$)"
)


def parse_code(title):
    """Pull the HCPCS / CPT code from the start of a ticket title.
    Returns the uppercased code or None if the title doesn't start with
    something code-shaped."""
    if not title:
        return None
    m = CODE_RE.match(title.strip())
    return m.group(1).upper() if m else None


ISSUES_QUERY = """
query Issues($projectId: String!, $cursor: String) {
  issues(
    first: 100
    after: $cursor
    filter: { project: { id: { eq: $projectId } } }
  ) {
    nodes {
      id
      identifier
      url
      title
      parent { id }
      labels { nodes { id name } }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


def fetch_all_issues(project_id, token, sleep_s=1.0):
    """Paginate through every issue in the given project. Returns a list
    of node dicts."""
    cursor = None
    out = []
    pages = 0
    while True:
        data = gql_with_retry(ISSUES_QUERY,
                              {"projectId": project_id, "cursor": cursor},
                              token)
        page = data["issues"]
        out.extend(page["nodes"])
        pages += 1
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
        time.sleep(sleep_s)
    return out, pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer_name")
    ap.add_argument("--sleep", type=float, default=1.0,
                    help="Sleep between paginated requests. Default 1.0.")
    args = ap.parse_args()

    cdir = customer_dir(args.customer_name)
    cfg = load_config(args.customer_name)
    token = get_token()

    # ---- 1. Build set of insurance projects from payor_matches.csv ----
    pm_path = os.path.join(cdir, "payor_matches.csv")
    if not os.path.exists(pm_path):
        sys.exit(f"missing {pm_path} — run match_payors.py first")

    project_map = {}  # uuid -> human name (for nicer logging)
    for r in csv.DictReader(open(pm_path)):
        u = (r.get("Project UUID") or "").strip()
        n = (r.get("Matched Project") or "").strip()
        if u:
            project_map[u] = n

    print(f"checking {len(project_map)} insurance projects for existing "
          f"parents...", file=sys.stderr)

    # ---- 2. Query each insurance project ----
    parent_rows = []
    for puuid, pname in sorted(project_map.items(), key=lambda x: x[1]):
        try:
            issues, pages = fetch_all_issues(puuid, token, args.sleep)
        except Exception as e:
            print(f"  FAIL {pname}: {e}", file=sys.stderr)
            continue
        # Parents = issues with no parent. Customer-side child tickets
        # live in the customer's Qual Criteria project, not in the
        # Insurance project — but in case someone has parented within
        # the Insurance project for any reason, we filter explicitly.
        parents = [i for i in issues
                   if not (i.get("parent") and i["parent"].get("id"))]
        kept = 0
        for iss in parents:
            code = parse_code(iss["title"])
            if not code:
                continue  # title doesn't start with a code → can't collide
            parent_rows.append({
                "Project UUID":    puuid,
                "Matched Project": pname,
                "Code":            code,
                "Title":           iss["title"],
                "Issue UUID":      iss["id"],
                "Issue ID":        iss["identifier"],
                "URL":             iss["url"],
            })
            kept += 1
        print(f"  {pname}: {len(parents)} parents ({kept} with codes) "
              f"in {pages} page(s)", file=sys.stderr)

    out_path = os.path.join(cdir, "existing_parents.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Project UUID", "Matched Project", "Code", "Title",
            "Issue UUID", "Issue ID", "URL"])
        w.writeheader()
        w.writerows(parent_rows)
    print(f"wrote {out_path} ({len(parent_rows)} existing parents)",
          file=sys.stderr)

    # ---- 3. Query customer's Qual Criteria project ----
    cust_proj = cfg.get("customer_project_id")
    if not cust_proj:
        print("\nno customer_project_id in config — skipping customer-side "
              "check", file=sys.stderr)
        return

    print(f"\nchecking customer Qual Criteria project for existing "
          f"tickets...", file=sys.stderr)
    try:
        cust_issues, pages = fetch_all_issues(cust_proj, token, args.sleep)
    except Exception as e:
        sys.exit(f"FAIL fetching customer project: {e}")

    cust_rows = []
    no_code = 0
    no_parent = 0
    for iss in cust_issues:
        code = parse_code(iss["title"])
        if not code:
            no_code += 1
            continue
        parent_id = ((iss.get("parent") or {}).get("id")) or ""
        if not parent_id:
            no_parent += 1
        labels_node = iss.get("labels") or {}
        labels = "|".join(
            l["name"] for l in (labels_node.get("nodes") or []))
        cust_rows.append({
            "Parent Issue UUID": parent_id,
            "Code":              code,
            "Title":             iss["title"],
            "Issue UUID":        iss["id"],
            "Issue ID":          iss["identifier"],
            "URL":               iss["url"],
            "Labels":            labels,
        })

    cpath = os.path.join(cdir, "existing_customer_tickets.csv")
    with open(cpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Parent Issue UUID", "Code", "Title",
            "Issue UUID", "Issue ID", "URL", "Labels"])
        w.writeheader()
        w.writerows(cust_rows)
    print(f"wrote {cpath} ({len(cust_rows)} existing customer tickets, "
          f"{no_code} skipped for no-code title, "
          f"{no_parent} have no parentId)", file=sys.stderr)


if __name__ == "__main__":
    main()
