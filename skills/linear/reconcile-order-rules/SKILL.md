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
version: 2.0.0
---

# Reconcile Order Rules → Linear

Compares built order rules (a "Service Line Order Type Codes" export) against Linear criteria
tickets and produces an actionable diff. **Read-only** — it never changes Linear.

## Inputs (durable, in `~/Claude/Projects/`)
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
`~/Claude/Projects/Criteria Updates/.recon_work/` and prints the exact mapper commands.

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
Outputs land in `~/Claude/Projects/Criteria Updates/`, date-stamped:
- `Order_Rule_Linear_Reconciliation_<date>.xlsx` — Summary + tabs: **FLIP → mark Done**,
  **NEW-TIX → create**, **CONFLICT → review**, **UNIT-GAP**, **DONE (in sync)**, and
  **Needs Review (order names)** (unresolved rows with order type name + ID for Bruna to map).
- `row_resolution_<date>.csv` — every row with its resolved project + basis + the Aug-2026 fields
  (`true_service_line`, `state`, `criteria_creator_name/email`).
- `Order_Type_Ticket_Map_<date>.csv` + `.xlsx` — the **per-row "Order Type → Ticket" map** (built by
  `scripts/build_map.py`). **Append-only schema:** raw export columns are preserved verbatim (incl.
  the original `v1_created_by_name`/`v1_created_by_email`); new signals are appended to the right —
  `hcpc`, `criteria_creator_*` (additive, never a replacement for `v1_created_by_*`), `state`,
  `true_service_line`, `resolved_project`/`project_uuid`/`resolution_basis`, and the Linear ticket
  join `verdict` + ticket id / **title** / state / URL. Published to the shared Google Sheet (Step 5b).
- `Ticket_Actions_<date>.csv` — the actionable slice, deduped per code/drug × project, with
  `true_service_line` + ticket title/state/URL. Published to the **Ticket Actions** Sheet, one tab per
  verdict: `FLIP → Done`, `NEW-TIX → create`, `CONFLICT → review`, `UNIT-GAP`.
- `Payer_Mapping_Needs_Review_<date>.csv` — low-confidence payer→project combos (confidence < 3) with
  the `validated` column. Published to the **Payer Mapping — Needs Review** Sheet.
- `Payer_Project_Mapping_<date>.xlsx` + `.csv` — the unique payer→project mapping with a **0–5
  confidence score**. One row per `(payer_family × insurance_payer × plan_category ×
  resolved_project)` combo, color-coded by confidence, sorted highest-confidence + highest-volume
  first. Confidence reflects the resolution layer that won: **5** crosswalk (source of truth),
  **4** family/category(+state) rule, **3** order-name mining / BCBS→Anthem fallback / strong
  name-mapper, **2** weaker name match, **0** unresolved. Last column **`order_type_names`** is
  populated *only when the order-rule name actually drove the mapping* (basis `ordername`, or a
  family+state resolution where the state came from the order name, not the payer). The
  **`validated`** column is the feedback round-trip (see Step 6). Built by
  `scripts/build_payer_mapping.py`.

Report the headline counts and point Bruna to the FLIP and Needs-Review tabs, plus the
payer→project mapping file.

**Aug-2026 export schema (35 cols):**
- **Service line = `mapped_service_lines` (col R)** when real, else `existing_service_line` (col Q),
  else blank — excludes `Unmapped`/`testing`. Computed as `true_service_line`. DME→R; Infusion's R is
  `Unmapped` so it falls back to Q (the drug name).
- **Attribution = `criteria_generation_user_*` (true author) → `v1_created_by_*` fallback.** Emitted as
  additive `criteria_creator_*` columns; `v1_created_by_*` are always preserved, never overwritten.
- **State = `order_rule_states` (H, e.g. `["OH"]`) → `criteria_generation_state_codes` (O).** Fed into
  the resolver so state-specific Medicaid-MCO / BCBS projects resolve even when the name omits state.
- **Crosswalk tag `ORDER_TYPE_NAME_ONLY`** — a coarse blank-payer key whose `linear_project` is this
  sentinel resolves from the order type name + state instead of a fixed project (avoids funneling many
  states to one project). A **state guard** also corrects any state-specific crosswalk hit whose state
  contradicts the row's H/O state.

### Step 5b — Publish to the shared Google Sheets (run with the venv python)
```bash
~/Claude/Projects/.venv-sheets/bin/python scripts/publish_map_to_sheets.py "<Order_Type_Ticket_Map_<date>.csv>"
~/Claude/Projects/.venv-sheets/bin/python scripts/publish_reconciliation_sheets.py
```
Sheet IDs live in `Linear Master Data/reconciliation_sheets.json` (`map`, `crosswalk`, `needs_review`,
`ticket_actions`). Auth is OAuth-as-user (cached token in `Credentials/google_sheets_token.json`; the
venv has `gspread`/`google-auth`/`google-auth-oauthlib`). ⚠️ The publisher does clear-then-write, so
`build_map` must only ever ADD to its `APPEND_COLUMNS` — never drop/reorder the base columns.

### Step 6 — Feedback loop (validated → crosswalk; Sheet is home)
The crosswalk lives in a shared Google Sheet (`payer_project_crosswalk`, id in
`reconciliation_sheets.json`) with `payer_project_crosswalk.csv` as its synced cache; its columns
include `resolution_mode` and `validated_by`. Run `apply_feedback.py` **with the venv python** so it
can sync: it **pulls** the Sheet first (honoring manual Sheet edits), applies validated rows, writes
the local CSV, then **pushes** back. `scripts/crosswalk_sheets.py push|pull` syncs standalone. The
crosswalk grows from Bruna's validated decisions. Two entry points, both write to the crosswalk and
win automatically on the next run:

- **From the payer→project mapping** (preferred): in `Payer_Project_Mapping_<date>.xlsx` (or
  `.csv`), Bruna fills the **`validated`** column, then feeds it back:
  ```bash
  ~/Claude/Projects/.venv-sheets/bin/python scripts/apply_feedback.py "<Payer_Project_Mapping_<date>.xlsx>" --by you@tennr.com   # add --dry-run to preview
  ```
  (Validate rows in the mapping file **or** directly in the crosswalk Google Sheet — the pull step
  ingests Sheet edits first. `--by` stamps `validated_by`; it defaults to bruna@tennr.com.)
  The `validated` cell is read three ways:
  - **truthy word** (`x`/`yes`/`y`/`✓`) — validate the row as-is (correct `resolved_project` in
    place first on low/zero-confidence rows). UUID comes from `project_uuid`, else looked up by
    project name (tolerant of `&`/`and`/case/punctuation, requiring a unique match).
  - **a Linear project UUID** — treated as **authoritative**: the canonical project name is pulled
    from that UUID, overriding the row's project column. Use this to resolve a blank row *or*
    correct a wrong auto-mapping in one step.
  - **"New Project Needed"** (any text containing "new project") — there is no existing Linear
    project to point at, so it is **not** crosswalked; instead it's collected into
    `New_Projects_Needed_<date>.csv` for project creation (see below).

  It appends/updates the matching `(family, payer, plan_category)` crosswalk entry, tags it
  `source = Bruna-validated`, backs up the crosswalk first, and is idempotent (re-feeding the same
  file is a no-op). Rows whose project/UUID can't be resolved are reported, not written.
- **New projects**: rows in `New_Projects_Needed_<date>.csv` need a Linear insurance project
  created first (via the Linear MCP), then the master-data cache refreshed so the new project lands
  in `insurance_projects.csv`; only then can those payers be validated into the crosswalk.
- **From the Needs-Review tab**: filling the `→ Correct Payer/Project` column and appending those
  rows to `payer_project_crosswalk.csv` (same columns) works too — same effect.

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
- The crosswalk grows over time and is authoritative — extend it (Step 6), don't re-derive from scratch.
- `scripts/resolver.py` holds the family/state/order-name logic (state-aware); `scripts/reconcile.py`
  is the entry point; `scripts/build_workbook.py` renders the reconciliation workbook;
  `scripts/build_payer_mapping.py` renders the payer→project mapping; `scripts/build_map.py` renders
  the per-row Order Type → Ticket map; `scripts/apply_feedback.py` promotes validated rows into the
  crosswalk. **Google Sheets** (run with the venv python): `scripts/sheets_io.py` (shared OAuth
  client), `scripts/publish_map_to_sheets.py`, `scripts/publish_reconciliation_sheets.py`,
  `scripts/crosswalk_sheets.py` (crosswalk push/pull). Sheet IDs: `Linear Master Data/reconciliation_sheets.json`.
- **Google Sheets deps:** a `~/Claude/Projects/.venv-sheets` virtualenv with `gspread`,
  `google-auth`, `google-auth-oauthlib` (+ `openpyxl` for reading `.xlsx` feedback files).
- See also memory: `payer-project-crosswalk`, `insurance-reconciliation-sop`, `order-type-ticket-map-sheet`.
