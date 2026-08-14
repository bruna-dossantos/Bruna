# scripts/linear

Reusable Linear utility scripts. Copied 2026-08-14 from `~/Documents/Claude/Projects/Linear Scripts/` and **sanitized** — every hardcoded Linear token was replaced with `os.environ["LINEAR_TOKEN"]`.

## ⚠️ Before running
Set your token in the shell (do NOT hardcode it):
```bash
export LINEAR_TOKEN="lin_api_..."   # from ~/Documents/Claude/Projects/Credentials/linear_tokens.json
```
Output paths in some scripts still point at `~/Desktop` / `~/Downloads` — change them to a project path before running.

## Scripts
| Script | What it does |
|--------|--------------|
| `customer_ids.py` | Pulls customers + their UUIDs from Linear → CSV |
| `customer_requests.py` | Pulls customer requests/needs → CSV |
| `get_team_label_uuids.py` | Team label → UUID lookup |
| `get_team_workflow_states_with_uuid.py` | Workflow states + UUIDs for a team |
| `get_unique_workflowstate_ids.py` | Unique workflow-state IDs |
| `payer_reconciliation/` | Payer→project reconciliation helpers (`reconcile2.py`, `hybrid.py`, `family_lib.py`, `build_workbook2.py`, `apply_final.py`) — overlaps with the `reconcile-order-rules` skill; consolidate later |

## Provenance
Originals remain in `~/Documents/Claude/Projects/Linear Scripts/` (with live tokens — see that folder's README and the rotation flag in `migration/ESTATE-MAP.md`).
