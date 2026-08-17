import requests
import time
import os

API_TOKEN = os.environ["LINEAR_API_TOKEN"]

DONE_STATE = {
    "INF3": "70436c7a-3cde-4040-81d4-9d3e1991aba0",
    "CRI":  "8a3bd861-900b-40d8-b70d-30418208103d",
    "QUA2": "d4f3320e-d0bc-41db-87b3-8d318f2db9bd",
}

ISSUES = [
    "INF3-20350", "INF3-20343", "INF3-20340",
    "CRI-45262", "CRI-45261", "CRI-45258", "CRI-45257", "CRI-45256",
    "CRI-45255", "CRI-45254", "CRI-45253", "CRI-45252", "CRI-45251",
    "CRI-45250", "CRI-45249", "CRI-45248", "CRI-45247", "CRI-45162",
    "QUA2-2025", "QUA2-2024", "QUA2-2023", "QUA2-2022",
    "CRI-44925", "CRI-44098", "CRI-32978", "CRI-27313", "CRI-25792",
    "CRI-25685", "CRI-25535", "CRI-25234", "CRI-25209", "CRI-25185",
    "CRI-25056", "CRI-25055", "CRI-24705", "CRI-24702", "CRI-24691",
    "CRI-24686", "CRI-24679", "CRI-24672", "CRI-24667", "CRI-24666",
    "CRI-24664", "CRI-24647", "CRI-24643", "CRI-24633", "CRI-24626",
    "CRI-24624", "CRI-24623", "CRI-24595", "CRI-24594", "CRI-24592",
    "CRI-24584", "CRI-24583", "CRI-24580", "CRI-24570", "CRI-24569",
    "CRI-24553", "CRI-24544", "CRI-24531", "CRI-24527", "CRI-24516",
    "CRI-24514", "CRI-24503", "CRI-24500", "CRI-24480", "CRI-24478",
    "CRI-24464", "CRI-24462", "CRI-24461", "CRI-24459", "CRI-24454",
    "CRI-24448", "CRI-24447", "CRI-24445", "CRI-24444", "CRI-24442",
    "CRI-24441", "CRI-24440", "CRI-24433", "CRI-24432", "CRI-24429",
    "CRI-24428", "CRI-24426", "CRI-24425", "CRI-24421", "CRI-24420",
    "CRI-24418", "CRI-24417", "CRI-24416", "CRI-24413", "CRI-24411",
    "CRI-24409", "CRI-24407", "CRI-24403", "CRI-24400", "CRI-24399",
    "CRI-24398", "CRI-24397", "CRI-24395", "CRI-24384", "CRI-24382",
    "CRI-22166", "CRI-22041", "CRI-21973", "CRI-19543", "CRI-4410",
]

# Step 1: resolve identifiers → UUIDs
FETCH_QUERY = """
query Issue($id: String!) {
  issue(id: $id) { id identifier }
}
"""

MUTATION = """
mutation IssueUpdate($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: { stateId: $stateId }) {
    success
    issue { id identifier state { name } }
  }
}
"""

def gql(query, variables):
    r = requests.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": API_TOKEN, "Content-Type": "application/json"},
        json={"query": query, "variables": variables},
    )
    return r.json()

success, failed = 0, []

for i, identifier in enumerate(ISSUES):
    team = identifier.split("-")[0]
    state_id = DONE_STATE[team]

    # Resolve identifier → UUID
    res = gql(FETCH_QUERY, {"id": identifier})
    if "errors" in res or not res.get("data", {}).get("issue"):
        print(f"[{i+1}/{len(ISSUES)}] FETCH FAIL {identifier}: {res.get('errors')}")
        failed.append((identifier, "fetch failed"))
        time.sleep(0.1)
        continue

    uuid = res["data"]["issue"]["id"]

    # Mark done
    res2 = gql(MUTATION, {"id": uuid, "stateId": state_id})
    if res2.get("data", {}).get("issueUpdate", {}).get("success"):
        state_name = res2["data"]["issueUpdate"]["issue"]["state"]["name"]
        print(f"[{i+1}/{len(ISSUES)}] OK  {identifier} → {state_name}")
        success += 1
    else:
        print(f"[{i+1}/{len(ISSUES)}] UPDATE FAIL {identifier}: {res2.get('errors')}")
        failed.append((identifier, res2.get("errors")))

    time.sleep(0.1)

print(f"\nDone: {success} marked complete, {len(failed)} failed")
if failed:
    for ident, err in failed:
        print(f"  {ident}: {err}")
