import os
import requests
import csv

API_KEY = os.environ["LINEAR_TOKEN"]  # sanitized: set in shell / Credentials; never hardcode
GRAPHQL_URL = "https://api.linear.app/graphql"
OUTPUT_FILE = "workflowstate_ids.csv"

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

# All teams
TEAMS = {
    "Qualifications": "63522420-9814-41d3-8775-48042c896c6e",
    "DME Criteria": "5a590300-221b-4e36-8df9-8210745571db",
    "Drug": "725f45f9-4f96-4f1a-a90c-92ff8a644f97",
    "Imaging": "a51f98b4-c379-4597-a13c-057711963a38",
    "Procedures and Services": "4781ac1f-a8c4-4f6a-b436-0040bef8f938"
}

all_rows = []

for team_name, team_id in TEAMS.items():
    query = f'''
    query {{
      team(id: "{team_id}") {{
        name
        states {{
          nodes {{
            id
            name
          }}
        }}
      }}
    }}
    '''

    response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query})
    response.raise_for_status()
    data = response.json()

    team = data["data"]["team"]
    states = team["states"]["nodes"]

    for state in states:
        all_rows.append([
            team_name,
            team_id,
            state["name"],
            state["id"]
        ])

# Write to CSV
with open(OUTPUT_FILE, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Team Name", "Team UUID", "Workflow State Name", "Workflow State UUID"])
    writer.writerows(all_rows)

print(f"\n✅ Done! {len(all_rows)} workflow state UUIDs exported across all teams.")
print(f"📁 Output saved to: {OUTPUT_FILE}")