import os
import requests
import csv

API_KEY = os.environ["LINEAR_TOKEN"]  # sanitized: set in shell / Credentials; never hardcode
TEAM_ID = "63522420-9814-41d3-8775-48042c896c6e"
GRAPHQL_URL = "https://api.linear.app/graphql"
OUTPUT_FILE = "team_workflow_states_with_uuid.csv"

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

query = f'''
query {{
  team(id: "{TEAM_ID}") {{
    workflowStates {{
      nodes {{
        id
        name
        type
        position
      }}
    }}
  }}
}}
'''

response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query})
response.raise_for_status()
data = response.json()

states = data["data"]["team"]["workflowStates"]["nodes"]

# Write to CSV
with open(OUTPUT_FILE, mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["Workflow State Name", "UUID", "Type", "Position"])
    writer.writeheader()
    for state in sorted(states, key=lambda x: x["position"]):
        writer.writerow({
            "Workflow State Name": state["name"],
            "UUID": state["id"],
            "Type": state.get("type", ""),
            "Position": state.get("position", "")
        })

print(f"\n✅ Done! {len(states)} workflow states exported.")
print(f"📁 Output saved to: {OUTPUT_FILE}")