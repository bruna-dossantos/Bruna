---
name: reconcile-order-rules
description: >
  Reconcile a Service-Line Order-Type Codes export (built order rules in Tennr) against the
  Linear criteria tickets, and figure out what changed: which tickets should move to Done, which
  code/drug × payer combos still need new tickets, and which conflict. Resolves each order rule's
  payer to a Linear project using Bruna's hand-validated crosswalk (source of truth) first, then
  family+category(+state) rules, order-type-name mining, the payer-linear-mapper skill's rules
  engine, and a LOB-guarded name fallback. Use when
  Bruna says "reconcile order rules", "run the order-rule reconciliation", "reconcile the order
  type export against Linear", "analyze the order type codes", "run the insurance reconciliation",
  or drops a "Service Line Order Type Codes" CSV and asks what's done / what tickets are needed.
  READ-ONLY — never writes to Linear. Ticket writes are a separate, explicitly-confirmed step.
version: 1.0.0
---

# Reconcile Order Rules → Linear

Compares built order rules (a "Service Line Order Type Codes" export) against Linear criteria
tickets and produces an actionable diff. **Read-only** — it never changes Linear.

## Inputs (durable, in `~/Documents/Claude/Projects/`)
- **Order-type export** (the input) — provided by Bruna, usually in `~/Downloads/`.
- **`Linear Master Data/payer_project_crosswalk.csv`** — Bruna's hand-validated payer→project
  mappings. **Source of truth; applied first.** Key: `(payer_family, insurance_payer, plan_category)`.
- **`Linear Master Data/insurance_projects.csv`** — project name→UUID (kept fresh by linear-master-data).
- **`Linear Master Data/insurance_initiative_issues_latest.csv`** — the Linear tickets export.

## Workflow

### Step 1 — Freshness gate (do this FIRST)
Check the age of `insurance_initiative_issues_latest.csv`.
- **> 7 days old** → run **`linear-ops:linear-master-data`** first. It refreshes the reference
  cache AND auto-chains **`criteria-toolkit:refresh-insurance-issues`**, which re-exports the
  tickets. Only then continue.
- **≤ 7 days** → proceed directly.
(The script also prints the age and warns if stale.)

### Step 2 — Prep payer lists
```bash
python3 scripts/reconcile.py --prep "<path to the order type export>.csv"
```
Writes `dme_payers_source.csv` + `inf_payers_source.csv` (distinct payers × volume) to
`~/Documents/Claude/Projects/Criteria Updates/.recon_work/` and prints the exact mapper commands.

### Step 3 — Run the payer-linear-mapper skill
Invoke **`payer-linear-mapper`** on each source list, writing its output back to `.recon_work/`:
```bash
map_payers.py --source ".recon_work/dme_payers_source.csv" --out ".recon_work/dme_mapping.csv" --projects "<insurance_projects.csv>" --service-line dme
map_payers.py --source ".recon_work/inf_payers_source.csv" --out ".recon_work/inf_mapping.csv" --projects "<insurance_projects.csv>" --service-line other
```
This is the name-based resolution layer (its rules engine covers BCBS state-brands, Anthem
rollups, MCO handling, etc.). It sits **below** the crosswalk — Bruna's overrides always win.
If skipped, the reconcile still runs but coverage is lower (~88% vs ~95%) and more payers land in
Needs Review.

### Step 4 — Run the reconciliation
```bash
python3 scripts/reconcile.py "<path to the order type export>.csv"
```
Resolution order per row: **crosswalk override → family+category(+state) → order-type-name mining
→ payer-linear-mapper output (conf ≥ 2) → LOB-guarded name normalizer**. The LOB guard never routes
an MA/Medicaid row into a commercial project. Anything unresolved is collected for review, never guessed.

### Step 5 — Deliver
Outputs land in `~/Documents/Claude/Projects/Criteria Updates/`, date-stamped:
- `Order_Rule_Linear_Reconciliation_<date>.xlsx` — Summary + tabs: **FLIP → mark Done**,
  **NEW-TIX → create**, **CONFLICT → review**, **UNIT-GAP**, **DONE (in sync)**, and
  **Needs Review (order names)** (unresolved rows with order type name + ID for Bruna to map).
- `row_resolution_<date>.csv` — every row with its resolved project + basis.

Report the headline counts and point Bruna to the FLIP and Needs-Review tabs.

### Step 6 — Feedback loop
When Bruna fills in the `→ Correct Payer/Project` column on the Needs-Review tab, append those
decisions to `payer_project_crosswalk.csv` (same columns). They become source of truth and are
applied automatically on the next run.

## Verdicts
- **DONE** — rule built, ticket already Done (in sync).
- **FLIP** — rule built, ticket Open (Not Started/In Progress/In Review) → move to Done.
- **CONFLICT** — rule built, ticket Canceled/Not-Covered/Blocked → human review.
- **NEW-TIX** — rule built, no ticket for this code/drug × payer → create.
- **UNIT-GAP** — code/drug not present in Linear under that title → naming/crosswalk gap.

## Writing changes to Linear (separate, gated)
This skill does NOT write. To apply FLIP→Done or create NEW-TIX, use
**`linear-ops:linear-sync-subissues`** (has the `issueUpdate` mutation; Done-state UUIDs live in
`Linear Master Data/workflow_states.csv`) — always after a live re-pull, a preview, and Bruna's
explicit confirmation. Start with FLIP→Done (lowest risk).

## Notes
- The crosswalk grows over time and is authoritative — extend it, don't re-derive from scratch.
- `scripts/resolver.py` holds the family/state/order-name logic; `scripts/reconcile.py` is the
  entry point; `scripts/build_workbook.py` renders the workbook.
- See also memory: `payer-project-crosswalk`, `insurance-reconciliation-sop`.
