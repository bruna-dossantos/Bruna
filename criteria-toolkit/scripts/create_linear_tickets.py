import openpyxl, requests, time, os

API_TOKEN = os.environ["LINEAR_API_TOKEN"]
XLSX_PATH = "/Users/brunadossantos/Downloads/New tickets needed.xlsx"

# Team IDs
CRI_TEAM  = "5a590300-221b-4e36-8df9-8210745571db"
INF3_TEAM = "725f45f9-4f96-4f1a-a90c-92ff8a644f97"

# Service line → CRI label IDs
CRI_LABELS = {
    "Bathroom Products":     ["1f66e4e9-c0fc-429d-9542-597a03adfbb1"],
    "Canes and Crutches":    ["ae58e2c7-3ad6-4692-b648-f5f64f0101a6"],
    "Complex Respiratory":   ["0b4078e8-d7f6-4803-9fa0-61a3e5c5aa58"],
    "Home Blood Glucose Monitor": ["f21fa88d-0079-45b4-bf01-3d7927240d0c"],
    "Hospital Bed":          ["b4573320-957d-40bd-af70-7ddc9633837f"],
    "Incontinence":          ["7a7702bb-1d04-4bb8-9ca4-d862a3f36dcd"],
    "Lymphedema":            ["20f7ec1c-a32b-49a4-a2f6-de78f66afe6e"],
    "Manual Wheelchairs":    ["ee5f616d-9602-4511-96f7-5f935049b762"],
    "Miscellaneous DME":     ["7a369dca-16ce-4d1b-88cd-bf944f8cc13c"],
    "Orthotics":             ["bb9cb177-706b-4e90-8a4a-f4ed94801e6f"],
    "Osteogenesis Stimulators": ["fa3b419c-9fee-462c-bdfc-f26879ee7eb3"],
    "Ostomy Supplies":       ["ff8837c7-8a17-46a0-be6e-2aa358edef67"],
    "Oxygen":                ["21e2b275-db0b-4e68-86d2-aa464739811d"],
    "Patient Lift":          ["d03382d8-d1ee-4543-b1b1-b300639735c8"],
    "Positive Airway Pressure (PAP) Devices": ["f9a3884c-d0da-4ca6-9554-11c02bbe583b"],
    "Positive Airway Pressure (PAP) Devices, Respiratory Assist Devices - BiPAP":
                             ["f9a3884c-d0da-4ca6-9554-11c02bbe583b",
                              "c6c612eb-5f2b-4d4e-b950-587a1f690bdc"],
    "Respiratory Assist Devices - BiPAP": ["c6c612eb-5f2b-4d4e-b950-587a1f690bdc"],
    "Tracheostomy":          ["a49280eb-0b8a-4da2-bfdb-da3a614a97d4"],
    "Ventilators":           ["26b9b997-e6f3-465e-8d26-c4d54f60c7a2"],
    "Walkers":               ["9b599fac-b57a-41e1-8ce6-01add2b9baf7"],
    "Wound Care":            ["45348aab-f735-427f-b957-8d2cd598e301"],
}

MUTATION = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier title }
  }
}
"""

def create_issue(title, team_id, project_id, label_ids):
    payload = {"title": title, "teamId": team_id, "projectId": project_id}
    if label_ids:
        payload["labelIds"] = label_ids
    r = requests.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": API_TOKEN, "Content-Type": "application/json"},
        json={"query": MUTATION, "variables": {"input": payload}},
    )
    data = r.json()
    if "errors" in data:
        return None, data["errors"]
    result = data["data"]["issueCreate"]
    if result["success"]:
        return result["issue"]["identifier"], None
    return None, "unknown failure"

wb = openpyxl.load_workbook(XLSX_PATH)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))[1:]

success, failed, no_label = 0, [], []

for i, row in enumerate(rows):
    hcpc, project_name, project_uuid, service_line = row

    if not hcpc or not project_uuid:
        print(f"[{i+1}/{len(rows)}] SKIP (missing data): {row}")
        continue

    # Route to team and get label IDs
    if str(hcpc) == "3245":  # tildrakizumab-asmn → INF3
        team_id = INF3_TEAM
        label_ids = []
        no_label.append(f"{hcpc} ({project_name})")
    else:
        team_id = CRI_TEAM
        label_ids = CRI_LABELS.get(service_line, [])
        if not label_ids:
            no_label.append(f"{hcpc} / {service_line} ({project_name})")

    identifier, err = create_issue(str(hcpc), team_id, project_uuid, label_ids)
    if identifier:
        print(f"[{i+1}/{len(rows)}] OK  {identifier}  {hcpc}  {project_name}")
        success += 1
    else:
        print(f"[{i+1}/{len(rows)}] FAIL  {hcpc}  {project_name}: {err}")
        failed.append((hcpc, project_name, err))

    time.sleep(0.12)

print(f"\nDone: {success} created, {len(failed)} failed")

if no_label:
    print(f"\nCreated without service line label ({len(no_label)}):")
    for x in no_label:
        print(f"  {x}")

if failed:
    print("\nFailed:")
    for hcpc, proj, err in failed:
        print(f"  {hcpc} / {proj}: {err}")
