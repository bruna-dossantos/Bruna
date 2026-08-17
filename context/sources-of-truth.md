# Sources of truth

When two places disagree, this is which one wins and where the authoritative copy lives.

## Payer → Linear project
- The **payer→project crosswalk** is the source of truth for mapping a payer to its Linear qualification-criteria project. Apply it FIRST in any reconciliation before falling back to name matching.
- Lives in `~/Claude/Projects/Linear Master Data/payer_project_crosswalk.csv`.

## Linear reference data (teams, insurance projects, workflow states, labels)
- Canonical copy in `~/Claude/Projects/Linear Master Data/`.
- Refresh the local cache first if it's more than ~7 days stale before analyzing; otherwise analyze directly. (Insurance-reconciliation SOP.)

## Criteria library
- Consolidated criteria `.md` files live under `~/Claude/Projects/Criteria Updates/Criteria Library` (after the 2026-07-22 cleanup).

## Order Type → Ticket map
- Shared native Google Sheet is the source of truth for the order-type → Linear-ticket map. Skills read/publish against that Sheet, not a local copy.

## HCPCS code → service line
- Google Sheet (mirrors Metabase card #12262) maps HCPCS code → service line.

## Mapping policy reminders
- DME / Traditional Medicare override; Anthem commercial roll-up; "a Medicaid MCO is not state Medicaid"; no line-of-business assumption without an explicit marker.

## Precedence rule (general)
Internal source of truth (above) > primary/official policy source > secondary source > explicitly-labeled inference. Never present inference as fact. See the researcher and qa-skeptic agents.
