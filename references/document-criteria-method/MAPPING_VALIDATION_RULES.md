# Mapping Validation Rules

Checks that verify work against `CANONICAL_CRITERIA_MAPPING_RULES.md` and
`JB_SPECIFIC_RULES.md`. Every check exists because that failure actually occurred
during the Jul 2026 build — these are regression tests, not hypotheticals.

Run order matters: **extraction → classification → mapping → output**. A defect
upstream invalidates every check downstream, so don't evaluate mapping quality until
the extraction gates pass.

Severity: **BLOCKER** = do not ship · **WARN** = investigate and explain ·
**INFO** = report the number.

---

## Gate 1 — Extraction integrity

Nothing below matters if the source was read wrong. All BLOCKER.

| # | Check | Pass condition | Why |
|---|---|---|---|
| 1.1 | Heading-variant recall | Every page whose text matches the loose Rx-heading pattern is either extracted or explicitly listed with a reason | 15 payers were missing on typos and zero-width spaces |
| 1.2 | Zero-width normalisation | No extracted text contains `​ ‌ ‍ ﻿ \xad` | broke both heading and value matching |
| 1.3 | No navigation as requirements | No extracted line matches the nav chrome list (`Site Contents`, `Northwood PA Project`, `Billing University`, …) | a reference page yielded 6 nav items as requirements |
| 1.4 | Section-boundary containment | <1% of extracted lines match post-Rx content (`AOB is required`, `Order confirmation`, `We can ship`, `Smart Action`) | section ran past its end |
| 1.5 | Value-vs-header discipline | No section is opened by a bare title-case `<li>` that has no following `<ul>`, no nested list, is not ALL-CAPS, and does not end in a colon | `Diabetes` in a diagnosis list opened a bogus Diabetic Testing section |
| 1.6 | Wrapped-value capture | Every `Provider Type` value that should read `Out of Network` does; none reads a truncated fragment (`OUT OF`) | 8 payers misclassified |
| 1.7 | HCPCS-vs-ICD guard | No diagnosis constraint contains a code derived from a known HCPCS supply code (`A4927`, `T4543`, `A4253`, `A5120`, `A6257`, `A4670`, `A4351-3`) | decimal-less normalisation invented 11 diagnoses |
| 1.8 | Cross-run line-count stability | Total extracted lines don't drop >2% versus the previous run without an explained cause | a `<2 items` filter silently dropped 22 pages |

**1.5 is the highest-value check.** It is the difference between a correct section tree
and content being attributed to the wrong product.

---

## Gate 2 — Classification integrity

| # | Check | Severity | Pass condition |
|---|---|---|---|
| 2.1 | J&B ownership | BLOCKER | every `J&B - *` doc, `Sample Choice`, and every `* Nursing Assessment` → Customer J&B; **zero** appear as payer-specific |
| 2.2 | Test fixtures excluded | BLOCKER | no criteria sourced from `Jasper Test`, `RX - Test`, `RX - InHealth Test`, `BetterNight - Demos` |
| 2.3 | Payer-ID provenance | WARN | HDMS Payer ID used where present; filename prefix only as fallback; count of blanks reported |
| 2.4 | No catch-all payer bucket | BLOCKER | no payer classified as generic `State Medicaid` — every one resolves to a named payer |
| 2.5 | Named MCOs beat state fallback | BLOCKER | `Blue Cross Complete MI Northwood Medicaid MCO` → Blue Cross Complete, not plain Michigan Medicaid |
| 2.6 | Case/format-insensitive state match | BLOCKER | `Fl Medicaid`, `Q8 Form - CO Medicaid` resolve to Florida / Colorado |
| 2.7 | Parent pages not counted as payers with gaps | WARN | pages with ≥2 linked children and no Rx are verdict `Parent page`, children tagged |
| 2.8 | Child plans are plans | BLOCKER | no child entry derived from a phone/fax/IVR line |
| 2.9 | Out-of-network correlation | INFO | payers with requirements skew In Network; report the ratio both ways as a sanity signal |

---

## Gate 3 — Canonical selection

| # | Check | Severity | Pass condition |
|---|---|---|---|
| 3.1 | Canonical Library wins | BLOCKER | where a Canonical Library criteria exists for a concept, it is the canonical pick |
| 3.2 | House format outranks terse | BLOCKER | no concept picks a definition with 0 house-format markers when a candidate with ≥2 exists |
| 3.3 | Form-bound never universal | BLOCKER | no criteria in a Universal tier contains form-bound wording |
| 3.4 | Soft positional not penalised | BLOCKER | "typically found towards the bottom", "may be labeled as X" are **not** flagged form-bound |
| 3.5 | Generic-source doesn't beat house format | BLOCKER | source scope is a tiebreaker only, never a substitute for wording quality |
| 3.6 | No ordinal words | BLOCKER | no criteria label or definition uses "primary"/"secondary" as a positional reference (domain use like "primary dressing" is exempt) |
| 3.7 | Complete concept library | BLOCKER | every universal label appears in canonical, including concepts that exist only on payer/customer documents |
| 3.8 | Proposals segregated | BLOCKER | drafted-but-unbuilt criteria are not mixed into the canonical sheet as if they existed |

---

## Gate 4 — Mapping correctness

The core gate. All BLOCKER unless noted.

| # | Check | Pass condition |
|---|---|---|
| 4.1 | **No GAP remains** | `GAP = 0`; any genuinely new concept is drafted and listed |
| 4.2 | Distinct fields stay distinct | Liter Flow / PO2 / Saturation, Test Date / Method / Results, PAP Settings / CPAP Supplies / Apnea Index are separate criteria |
| 4.3 | Timeframes not merged | recency criteria differing only by 30/60/90 days / 6 months / 1 year are separate; timeframe derived from **definition**, not label |
| 4.4 | Identifier types not merged | Medicaid ID ≠ Insurance ID; NPI ≠ License ≠ Texas Provider ID |
| 4.5 | Diagnosis roles not merged | Diagnosis / Code-ICD10 / Primary / Secondary / Supporting / Type of Incontinence / Underlying Cause resolve separately |
| 4.6 | **Compound requirements fully split** | for each compound pattern, **both** criteria appear on the document with the same source text |
| 4.7 | Compound doesn't override specific | `Duration/Refills - max 12 months` keeps `Length of Need - 12 Month Max (Accepts 99)`; never falls back to generic `Length of Need` |
| 4.8 | Negative rules keep the requirement | `Electronic and stamped signatures are NOT accepted` → `Prescriber Signature` |
| 4.9 | DX code lists preserved | no line carrying an ICD list maps to generic `Diagnosis`; each distinct list is its own criteria |
| 4.10 | Near-identical lists separate | `E08-E13.9` and `E10-E13.9` are two criteria |
| 4.11 | Allowlist semantics | required-list definitions state that extra diagnoses don't fail the order |
| 4.12 | Exclusion semantics | single-code exclusions state "regardless of whether other diagnoses are also documented" |
| 4.13 | Section-aware naming | `Name`/`Address` resolve to Patient in member sections, Prescriber in physician sections |
| 4.14 | Qualifier beats section | `Member Full Name` in the Physician section → Patient Name |
| 4.15 | Section-agnostic fields | Signature, Signature Date, PSL resolve wherever they appear |
| 4.16 | Non-Rx excluded | PA triggers, coverage limits, age rules, ops workflow are `NOT RX`, not requirements |
| 4.17 | Field-requirement guard | a line naming a required field is kept even when it also mentions a PA consequence |
| 4.18 | Wisconsin incontinence routing | `condition … or type of incontinence` → `Supporting (Incontinence)`, not Underlying Cause |
| 4.19 | Medicare SWO completeness | each Medicare-deferred payer carries all 6 SWO elements; unbuilt ones show as pending, not omitted |
| 4.20 | Medicare incontinence exclusion | no Medicare-deferred payer has an incontinence document |
| 4.21 | Every alias resolves | renamed criteria (`Insulin Dependence` → `Insulin Dependency Status`) point at live IDs; no stale references |
| 4.22 | *(WARN)* UNMAPPED accounted for | ≤3% of lines, each reviewable with source text; never loosely mapped to clear the count |

---

## Gate 5 — Output integrity

| # | Check | Severity | Pass condition |
|---|---|---|---|
| 5.1 | Every row auditable | BLOCKER | 100% of rows carry verbatim source text + section |
| 5.2 | Links resolve | BLOCKER | every linked HTML file exists on disk; count reported |
| 5.3 | Synthesised rows declared | WARN | rows with no source line (Medicare SWO) are identifiable, not silently blank |
| 5.4 | Criteria IDs valid | BLOCKER | every non-pending criteria ID exists in the current canonical export |
| 5.5 | Base repeats consistently | BLOCKER | the same base criteria set appears on every document for a payer |
| 5.6 | Layer labelled | BLOCKER | every row marked Base or Product |
| 5.7 | Reviewer annotations survive | BLOCKER | Bruna's Category/Comment columns persist across every rebuild, keyed by requirement text |
| 5.8 | Review notes survive | BLOCKER | canonical review notes persist, keyed by Criteria ID |
| 5.9 | No silent truncation | WARN | anything capped (top-N, "+N more") states what was dropped |
| 5.10 | Coverage denominator honest | BLOCKER | `NOT RX` / `POLICY` / `REFERENCE` excluded from % coverage |

---

## Gate 6 — Cross-run regression

Run against the previous output. All WARN unless a drop is unexplained.

| # | Check | Pass condition |
|---|---|---|
| 6.1 | Payer count | doesn't fall; increases explained |
| 6.2 | Line count | doesn't fall >2% unexplained |
| 6.3 | Per-section counts | no section loses >10% of its payers unexplained (caught the header-detection regression: Incontinence 197→108) |
| 6.4 | BUILT count | doesn't fall (caught the compound rule overriding specific labels: 2,433→1,955) |
| 6.5 | Criteria-ID freshness | after a canonical rebuild, no row references a superseded ID |
| 6.6 | Concept count | canonical concepts don't fall; deletions explained |

---

## The five questions that caught the most defects

Ask these of any mapping before accepting it:

1. **Does this requirement name more than one field?** → §6 compound. Caught ~1,900
   dropped requirements.
2. **Would a different value on the page satisfy this vs. the criteria I chose?** → if
   yes they're different criteria. Caught the PAP/Oxygen over-merge.
3. **Is there a number, code list, or timeframe in the source that my criteria
   doesn't carry?** → the constraint is being lost. Caught 29 DX constraints.
4. **Is this a field to extract, or a policy about servicing?** → caught the T4543 PA
   rule mapping to Quantity Ordered.
5. **Did I pick this definition because it's better, or because its source document
   was generic?** → caught the house-format regression.

---

## Reporting format

State counts, not adjectives. For every gate:

```
Gate 4 — Mapping correctness
  4.1  GAP = 0                                    PASS
  4.6  compound split: 720 rows produce 2+        PASS
  4.9  DX lists: 29 constraints, 0 generic        PASS
  4.22 UNMAPPED 311 / 12,736 (2.4%)               WARN — listed with source text
```

If a check fails, say which, with the count and an example. If a check couldn't be
run, say that rather than implying it passed. Never report a gate as passing on the
strength of a spot check — the numbers are cheap to compute and the spot check is
what hid the `Diabetes`-as-header defect for several turns.
