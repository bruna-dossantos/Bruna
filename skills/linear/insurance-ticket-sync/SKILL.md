---
name: insurance-ticket-sync
description: >
  Weekly insurance criteria ticket sync for DME. Checks master data freshness, optionally
  refreshes it, cross-references an uploaded completed-codes CSV against current Linear tickets,
  shows a summary of gaps (new tickets needed + existing tickets to update), then executes
  the changes. Triggers on: "sync insurance tickets", "run the weekly sync", "weekly criteria
  sync", "update criteria tickets", "check CWT", "what tickets need to be created",
  "run the insurance ticket sync".
---

# Insurance Ticket Sync

Produces two lists from a completed-codes CSV and the Linear master data, then executes:
1. **CWT** (Completed Without Tickets) — create new Done/XS tickets in the right project
2. **Needs-Update** — move existing DME Criteria tickets to Done

---

## Constants

| | |
|---|---|
| Master data dir | `~/Claude/Projects/Linear Master Data/` |
| Issues export meta | `insurance_initiative_export_metadata.json` |
| Issues CSV | `insurance_initiative_issues_latest.csv` |
| Analysis script | `criteria-toolkit/scripts/analyze_insurance_tickets.py` |
| DME team | DME Criteria |
| Done state | Done |
| Estimate | XS |
| Stale threshold | 7 days |

---

## Step 1 — Check master data freshness

Read `~/Claude/Projects/Linear Master Data/insurance_initiative_export_metadata.json`.

Show the user:
> Master data last exported: **{last_export}** ({N} issues)

If the export is older than 7 days:
> ⚠️ Issues export is {X} days old. Recommend refreshing before continuing.

Offer two refresh options:
- **Issues only** (faster, ~2 min): invoke `criteria-toolkit:refresh-insurance-issues`
- **Full refresh** (reference data + issues): invoke `linear-ops:linear-master-data` first, then `criteria-toolkit:refresh-insurance-issues`

Wait for the user to decide, then continue.

---

## Step 2 — Get the completed-codes CSV

Ask the user to provide the path to their completed-codes CSV:
> Please provide the path to the completed-codes CSV (you can drag it in or paste the path).

The CSV must have these columns (column order doesn't matter):
- `code` — HCPC code (may have suffix like "A4351-UHC Medicaid OH"; script normalizes to 5-char)
- `insurance_payer_id` — payer Tennr UUID (may be blank for some MCO payers)
- `plan_category` — e.g., COMMERCIAL, MEDICAID, MEDICARE ADVANTAGE
- `order_rule_name` — used for keyword UUID resolution on blank-UUID MCO rows
- `v1_created_by_email` — assigned to this person when creating the ticket

---

## Step 3 — Run analysis

```bash
python3 criteria-toolkit/scripts/analyze_insurance_tickets.py "<csv_path>"
```

The script outputs a summary JSON to stdout and writes a full report to `<csv_path>.report.json`.

Parse the stdout JSON and show the user:

```
📊 Analysis complete
  Master data: {last_export}

  New tickets to create (CWT): {cwt_count}
  Existing tickets to update:  {needs_update_count}

  New tickets by project (top 10):
    Medicaid New York     — 42
    Aetna                 — 31
    ...

  Tickets to update by current state:
    In Progress           — 12
    Backlog               — 8
    ...
```

If both counts are 0, tell the user everything is already in sync and stop.

---

## Step 4 — Confirm

Ask the user:
> Ready to create {cwt_count} tickets and update {needs_update_count} tickets to Done. Proceed?

If no, stop. If yes, continue.

---

## Step 5 — Create CWT tickets

Read the full report JSON (`<csv_path>.report.json`) — the `cwt` array.

For each entry in `cwt`, call `save_issue` with:
- `title`: the `hcpc` value
- `team`: "DME Criteria"
- `project`: the `project` value
- `state`: "Done"
- `estimate`: 1 (XS)
- `assignee`: the `email` value (omit if blank)

Run in parallel batches. After all complete, report how many succeeded.

---

## Step 6 — Update Needs-Update tickets

Read the `needs_update` array from the report JSON.

For each entry, call `save_issue` with:
- `id`: the `identifier` value (e.g., CRI-12345)
- `state`: "Done"

Run in parallel batches. After all complete, report how many succeeded.

---

## Step 7 — Summary

Show a clean final summary:
```
✅ Sync complete
  Created:  {N} new tickets
  Updated:  {N} tickets → Done
  Failed:   {N} (list identifiers if any)
```

---

## Notes

**Keyword UUID overrides** — these blank-UUID MCO payers are resolved by matching `order_rule_name`:

| Keyword | Project UUID |
|---|---|
| UHC Community Medicaid MCO - Nebraska | 7576fb13-... |
| Nebraska Total Care | 69f8b563-... |
| UHC Community Medicaid MCO OH | cdbfe311-... |
| UHC Medicaid MCO OH | cdbfe311-... |
| UHC OH Dual Plan | 5d259896-... |
| Centene Medicaid MCO OH | ff951b98-... |
| Centene OH Medicaid/Buckeye Health Plan | ff951b98-... |

To add a new MCO payer, add a row to `_ORULE_UUID_MAP` in `analyze_insurance_tickets.py`.

**Blank-UUID Commercial rows** are always skipped — they can't be attributed to a project.

**Deduplication** — the script deduplicates CWT by (HCPC, project), so if a code appears under multiple order rules for the same payer, only one ticket is created.
