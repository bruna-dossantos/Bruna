---
name: refresh-insurance-issues
description: >
  Refreshes the insurance initiative issues export from Linear — pulls all current tickets
  under the Insurance initiative and writes insurance_initiative_issues_latest.csv to the
  Linear Master Data directory. Run this before any weekly sync or analysis when the export
  is stale (>7 days old). Triggers on: "refresh insurance issues", "update insurance issues",
  "pull fresh issues", "export insurance tickets", "update the issues CSV", "refresh the issues export".
---

# Refresh Insurance Issues

Pulls a fresh export of all issues in the Insurance initiative from Linear and updates the
master data CSVs used by `analyze_insurance_tickets.py`.

---

## What this skill does vs. `linear-master-data`

| Skill | Updates |
|---|---|
| `linear-ops:linear-master-data` | Reference data: teams, projects, workflow states, labels |
| **`criteria-toolkit:refresh-insurance-issues`** | Issue tickets: `insurance_initiative_issues_latest.csv` + timestamped snapshot |

Both are needed before a weekly sync. Run `linear-master-data` first if reference data is
stale, then run this skill to get fresh tickets.

---

## Constants

| | |
|---|---|
| Script | `criteria-toolkit/scripts/refresh_insurance_issues.py` |
| Output dir | `~/Claude/Projects/Linear Master Data/` |
| Issues CSV | `insurance_initiative_issues_latest.csv` |
| Export metadata | `insurance_initiative_export_metadata.json` |
| Stale threshold | 7 days |
| Initiative ID | `3f3a1212-8cb2-4afe-bcd5-4c8b8f0104de` |

---

## Step 1 — Check current staleness

Read `~/Claude/Projects/Linear Master Data/insurance_initiative_export_metadata.json`.

Show:
> Issues export last refreshed: **{last_export}** ({n_issues} issues)

If older than 7 days:
> ⚠️ Export is {X} days old — refreshing now.

If within 7 days, confirm with the user before re-running:
> Export is only {X} days old. Refresh anyway?

---

## Step 2 — Run the export

```bash
python3 criteria-toolkit/scripts/refresh_insurance_issues.py
```

This takes ~2 minutes (16k+ issues across ~65 pages). Show progress as it runs.

---

## Step 3 — Report

After the script completes, show:

```
✅ Issues export refreshed
  Issues pulled:  {N}
  Snapshot file:  insurance_initiative_issues_{timestamp}.csv
  Latest updated: insurance_initiative_issues_latest.csv
```

---

## Notes

- The script authenticates using `~/Claude/Projects/Credentials/linear_tokens.json`
- Both the timestamped file and `latest.csv` are written — the timestamped one serves as a
  historical record; `analyze_insurance_tickets.py` always reads `latest.csv`
- The Insurance initiative ID is hardcoded in the script (`3f3a1212-8cb2-4afe-bcd5-4c8b8f0104de`)
