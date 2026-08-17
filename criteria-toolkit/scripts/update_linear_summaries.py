import openpyxl
import requests
import time
import sys
import os

API_TOKEN = os.environ["LINEAR_API_TOKEN"]
XLSX_PATH = "/Users/brunadossantos/Downloads/Payor Mapping Linear Insurance.xlsx"

MUTATION = """
mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
    success
    project { id }
  }
}
"""

def update_project(project_id, summary):
    resp = requests.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": API_TOKEN, "Content-Type": "application/json"},
        json={"query": MUTATION, "variables": {"id": project_id, "input": {"description": summary}}},
    )
    data = resp.json()
    if "errors" in data:
        return False, data["errors"]
    return data["data"]["projectUpdate"]["success"], None

def main():
    wb = openpyxl.load_workbook(XLSX_PATH)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))[1:]  # skip header

    success_count = 0
    fail_count = 0
    failures = []

    for i, row in enumerate(rows):
        name       = row[0]
        uuid       = row[1]
        eclaim_id  = row[2]
        alias_id   = row[3]
        tennr_id   = row[4]
        category   = row[5]

        if not uuid or str(uuid).startswith('#'):
            print(f"[{i+1}/{len(rows)}] SKIP (no UUID): {name}")
            continue

        # Only re-run rows that have at least one null field
        if all(v is not None for v in [eclaim_id, alias_id, tennr_id, category]):
            continue

        eclaim_str = str(eclaim_id) if eclaim_id is not None else "Not Applicable"
        alias_str  = str(alias_id)  if alias_id  is not None else "Not Applicable"
        tennr_str  = str(tennr_id)  if tennr_id  is not None else "Not Applicable"
        cat_str    = str(category)  if category  is not None else "Not Applicable"

        summary = (
            f"Primary Payer E-Claim ID: {eclaim_str} / "
            f"Primary Payer Tennr ID: {tennr_str} / "
            f"Alias Payer ID: {alias_str} / "
            f"Payer Category: {cat_str}"
        )

        ok, err = update_project(uuid, summary)
        if ok:
            success_count += 1
            print(f"[{i+1}/{len(rows)}] OK  {name}")
        else:
            fail_count += 1
            failures.append((uuid, name, err))
            print(f"[{i+1}/{len(rows)}] FAIL {name}: {err}")

        # Stay well under Linear's rate limit (~100 req/10s)
        time.sleep(0.15)

    print(f"\nDone: {success_count} updated, {fail_count} failed")
    if failures:
        print("\nFailed projects:")
        for uuid, name, err in failures:
            print(f"  {uuid}  {name}  {err}")

if __name__ == "__main__":
    main()
