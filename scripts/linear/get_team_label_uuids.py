import os
import requests
import csv

API_KEY = os.environ["LINEAR_TOKEN"]  # sanitized: set in shell / Credentials; never hardcode
TEAM_ID = "63522420-9814-41d3-8775-48042c896c6e"

GRAPHQL_URL = "https://api.linear.app/graphql"
OUTPUT_FILE = "team_labels_with_uuid_filtered.csv"

ALLOWED_COLORS = {"#5e6ad2", "#4cb782"}

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

query = """
query ($teamId: ID!, $cursor: String) {
  issueLabels(first: 250, after: $cursor, filter: { team: { id: { eq: $teamId } } }) {
    nodes {
      id
      name
      color
      description
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

def normalize_hex(color):
    if not color:
        return ""
    c = color.strip().lower()
    if not c.startswith("#"):
        c = "#" + c
    return c


cursor = None
page = 0
total_seen = 0
filtered_labels = []

while True:

    page += 1

    response = requests.post(
        GRAPHQL_URL,
        headers=headers,
        json={
            "query": query,
            "variables": {
                "teamId": TEAM_ID,
                "cursor": cursor
            }
        },
        timeout=30
    )

    if response.status_code != 200:
        print("API response:", response.text)
        response.raise_for_status()

    data = response.json()

    labels_conn = data["data"]["issueLabels"]

    nodes = labels_conn["nodes"]
    page_info = labels_conn["pageInfo"]

    has_next = page_info["hasNextPage"]
    end_cursor = page_info["endCursor"]

    total_seen += len(nodes)

    for label in nodes:

        color = normalize_hex(label.get("color"))

        if color in ALLOWED_COLORS:
            filtered_labels.append({
                "Label Name": label["name"],
                "UUID": label["id"],
                "Color": color,
                "Description": label.get("description") or ""
            })

    print(
        f"Page {page}: fetched {len(nodes)} labels | "
        f"total seen {total_seen} | "
        f"filtered {len(filtered_labels)} | "
        f"hasNextPage={has_next}"
    )

    if not has_next:
        break

    cursor = end_cursor


with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["Label Name", "UUID", "Color", "Description"]
    )
    writer.writeheader()
    writer.writerows(filtered_labels)

print("\nExport complete.")
print(f"{len(filtered_labels)} labels saved to {OUTPUT_FILE}")