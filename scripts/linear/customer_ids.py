import os
import requests
import csv

ACCESS_TOKEN = os.environ["LINEAR_TOKEN"]  # sanitized: set in shell / Credentials; never hardcode
GRAPHQL_URL = "https://api.linear.app/graphql"
OUTPUT_FILE = "/Users/brunadossantos/Desktop/customers_with_uuid.csv"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

query = """
query ($cursor: String) {
  customers(first: 250, after: $cursor) {
    nodes {
      id
      name
      externalIds
      domains
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
all_customers = []

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

    customers_conn = data["data"]["customers"]
    nodes = customers_conn["nodes"]
    page_info = customers_conn["pageInfo"]
    has_next = page_info["hasNextPage"]
    end_cursor = page_info["endCursor"]

    total_seen += len(nodes)

    for customer in nodes:
        all_customers.append({
            "Customer Name": customer["name"],
            "UUID": customer["id"],
            "External IDs": ", ".join(customer.get("externalIds") or []),
            "Domains": ", ".join(customer.get("domains") or []),
        })

    print(
        f"Page {page}: fetched {len(nodes)} customers | "
        f"total seen {total_seen} | "
        f"hasNextPage={has_next}"
    )

    if not has_next:
        break
    cursor = end_cursor

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["Customer Name", "UUID", "External IDs", "Domains"]
    )
    writer.writeheader()
    writer.writerows(all_customers)

print("\nExport complete.")
print(f"{len(all_customers)} customers saved to {OUTPUT_FILE}")