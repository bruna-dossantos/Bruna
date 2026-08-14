import os
import requests
import csv

ACCESS_TOKEN = os.environ["LINEAR_TOKEN"]  # sanitized: set in shell / Credentials; never hardcode
GRAPHQL_URL = "https://api.linear.app/graphql"
OUTPUT_FILE = "/Users/brunadossantos/Desktop/customer_requests.csv"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

query = """
query ($cursor: String) {
  customerNeeds(first: 250, after: $cursor) {
    nodes {
      id
      body
      priority
      createdAt
      updatedAt
      customer {
        id
        name
      }
      issue {
        id
        title
        status: state {
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

cursor = None
page = 0
total_seen = 0
all_requests = []

while True:
    page += 1
    response = requests.post(
        GRAPHQL_URL,
        headers=headers,
        json={"query": query, "variables": {"cursor": cursor}},
        timeout=30
    )

    if response.status_code != 200:
        print("API response:", response.text)
        response.raise_for_status()

    data = response.json()

    if "errors" in data:
        print("GraphQL errors:", data["errors"])
        break

    conn = data["data"]["customerNeeds"]
    nodes = conn["nodes"]
    page_info = conn["pageInfo"]
    has_next = page_info["hasNextPage"]
    end_cursor = page_info["endCursor"]

    total_seen += len(nodes)

    for req in nodes:
        customer = req.get("customer") or {}
        issue = req.get("issue") or {}
        status = issue.get("status") or {}
        all_requests.append({
            "Request ID": req["id"],
            "Body": req.get("body") or "",
            "Priority": req.get("priority") or "",
            "Created At": req.get("createdAt") or "",
            "Updated At": req.get("updatedAt") or "",
            "Customer Name": customer.get("name") or "",
            "Customer UUID": customer.get("id") or "",
            "Issue ID": issue.get("id") or "",
            "Issue Title": issue.get("title") or "",
            "Issue Status": status.get("name") or "",
        })

    print(
        f"Page {page}: fetched {len(nodes)} requests | "
        f"total seen {total_seen} | "
        f"hasNextPage={has_next}"
    )

    if not has_next:
        break
    cursor = end_cursor

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Request ID", "Body", "Priority", "Created At", "Updated At",
        "Customer Name", "Customer UUID", "Issue ID", "Issue Title", "Issue Status"
    ])
    writer.writeheader()
    writer.writerows(all_requests)

print("\nExport complete.")
print(f"{len(all_requests)} requests saved to {OUTPUT_FILE}")