---
name: denial-analysis
description: Analyze healthcare claim denials to find root causes and preventable-denial opportunities. Use when the request is about denial reporting, denial trends, denials by payer/product/service-line, preventability, or operational recommendations tied to denied claims. Produces a structured, executive-friendly readout (Summary / Key Findings / Root Cause Hypothesis / Recommended Next Steps / Open Questions).
---

# Denial analysis

Reusable method for turning denial data into actionable operational insight. Runs under the **rcm-analyst** agent; hand clinical/medical-necessity judgment to **healthcare-sme** and pure numeric validation to **data-analyst**.

## The four questions every analysis answers
1. **What is happening?** — trend, denial volume, denial rate, payer/product concentration.
2. **Where is it happening?** — break down by payer, product category, service line, order type, payer level, invoice status.
3. **Why might it be happening?** — tie to documentation, eligibility, prior auth, payer requirements, qualification logic, billing errors, admin workflows, or payer behavior.
4. **What should we do next?** — clear recommendations and next steps.

## Denial categories (group reasons into these)
| Category | Description |
|----------|-------------|
| Eligibility / Coverage | Not eligible, not covered, benefit limitation |
| Prior Authorization | PA missing, denied, expired, or not matching the billed item |
| Documentation | Missing/incomplete/outdated records, Rx, LMNs, CMNs |
| Medical Necessity | Criteria not met, dx doesn't support item, clinical need unsupported |
| Billing / Coding | Wrong HCPCS, modifier, dx, units, place of service, payer level |
| Administrative / Billing Ops | Duplicates, resubmissions, posting errors, preventable handling |
| Contracting / Network | Not contracted, wrong billing entity, capitated group |
| Timely Filing | Past payer or appeal deadline |
| Coordination of Benefits | COB issue, wrong payer order, missing primary |
| Patient Responsibility | Deductible, copay, coinsurance, non-covered liability |
| Payer Behavior / Other | Payer-specific, unclear, or inconsistent denial |

## Preventability
Preventable / Partially Preventable / Not Preventable / Needs Review — judge whether better eligibility checks, documentation, PA, billing setup, or workflow could have avoided it. Payer-driven, patient-responsibility, and coverage exclusions are Not Preventable.

## Data fields & metrics
Useful fields: denial reason & category, invoice ID, order ID, payer name & level, product category, service line, HCPCS, status, dates (service/posted/billing), allowed/billed/paid/adjustment amounts, E&B run ID + decision, PA/documentation/qualification status.
Report **counts AND financial impact**: total denied claims, denied allowed/billed $, denial rate, by month/payer/product, top reasons & categories, MoM change, preventable volume & dollars.

## Output format
`Summary` (one key finding) → `Key Findings` (bullets) → `Root Cause Hypothesis` (practical) → `Recommended Next Steps` (action items) → `Open Questions`.
Use direct language ("This suggests…", "The highest-risk area appears to be…", "Recommended next step…"). Avoid "there may be some issues" / "this is interesting" / "more research needed" without saying exactly what to review and why. Keep it executive-friendly and plain-English.

## Source
Method extracted 2026-08-14 from `~/Claude/Projects/Denial Analyzer/AGENTS.md` (project brief). Project-specific data (CARC/RARC lists, write-off files) stays in that project — see its `PROJECT.md`.
