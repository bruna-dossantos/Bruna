# What's J&B, and what could become a general skill

*The split described here is now reflected in the folder layout: this folder holds the
portable half, `../J&B Document Criteria/` holds the customer instance.*

Every file in this project, sorted by whether it's **J&B output** or **reusable method**.

The short version: **the method is reusable, the data isn't.** Nothing about reading a payer
wiki, mapping requirements to criteria, or collapsing payers into a minimal document set is
specific to J&B. What's J&B is the cache it reads, the exports it merges, and a handful of
constants.

---

## Group 1 — J&B output. Regenerated, never edited by hand, not reusable

| File | |
|---|---|
| `JB_payer_prescription_requirements.xlsx` | J&B's 581 payers × their criteria |
| `JB_payer_service_line_matrix.xlsx` | J&B payer × service line → document |
| `JB_rx_requirements_criteria_gap_analysis.xlsx` | J&B requirements vs criteria, + review queue |
| `JB_prescription_requirements_by_item_type.md` | J&B requirements verbatim |
| `Canonical_Library.xlsx` | mostly reusable *content* (323 of 330 criteria are portable) but it is a snapshot of the Tennr library at a point in time |
| `validation_report_latest.txt` | the last run's numbers |

## Group 2 — reusable method. This is what a general skill would be built from

| File | Reusable? | What's J&B in it |
|---|---|---|
| `CANONICAL_CRITERIA_MAPPING_RULES.md` | **fully** | nothing — now in `Document Criteria Method/` |
| `MAPPING_VALIDATION_RULES.md` | **fully** | nothing — now in `Document Criteria Method/` |
| `JB_SPECIFIC_RULES.md` | **no** | this file *is* the customer-specific half; it stays in the J&B folder |
| `_pipeline/rxproj/dx_codes.py` | **fully** — 0 J&B refs | — |
| `_pipeline/rxproj/doc_versions.py` | **fully** — 0 J&B refs | — |
| `_pipeline/regen_canon.py` | **fully** — 0 J&B refs | — |
| `_pipeline/rxproj/extract.py` | reusable | *(lost in the temp-dir reap; rx_extracted.json was rebuilt from mapped_rows)* |
| `_pipeline/rxproj/plan_info.py` | reusable | 1 constant: `CACHE` path |
| `_pipeline/rxproj/make_matrix.py` | reusable | 1 constant: output path |
| `_pipeline/rxproj/make_md.py` | reusable | output path + title |
| `_pipeline/rxproj/make_xlsx.py` | reusable | output path |
| `_pipeline/rxproj/map_criteria.py` | reusable | 5 refs — see below |
| `_pipeline/rxproj/payer_docs.py` | reusable | 8 refs — cache path, `J&B - ` document prefix |
| `_pipeline/build_dedup.py` | reusable | 22 refs — `is_jb_doc`, `TEST_DOCS`, `PINNED_BY_LABEL` |
| `_pipeline/validate.py` | reusable | 18 refs — mostly J&B-specific probe cases inside checks |
| `_pipeline/rxproj/make_library.py` | reusable | 50 refs — the portable/J&B split, guard patterns |

---

## The seven things a general skill would need as inputs, not constants

Everything J&B-specific in the pipeline reduces to these. Parameterise them and the same
code runs for any customer.

| Today, hardcoded | Would become |
|---|---|
| `CACHE` / `CACHE_DIR` → the J&B wiki scrape | **path to this customer's page cache** |
| `CSV_IN` / `CSV_NEW` → the two Tennr exports | **path to the criteria exports** |
| `OUT` paths on 6 scripts | **output directory** |
| `is_jb_doc()` — `J&B - *`, `Sample Choice`, `*Nursing Assessment*` | **which document-name patterns mean "this customer owns it"** |
| `TEST_DOCS` — 4 fixtures to exclude | **test/demo documents to exclude** |
| `JB_WORDED` — `j&b`, `pontiac trail`, `737-00` | **the supplier's own name, address and receiving numbers**, so the contact-field guard and the portable/J&B split both work generically |
| `PINNED_BY_LABEL` | **which criteria the reviewer has declared the survivor** |

Plus one structural assumption worth naming: the extractor understands *this* wiki's shape —
a plan-info block, then `Prescription Requirements` / `Physician Requirements` / `DX
Requirements` sections in nested `<ul>`s. A different customer's source would need its own
extractor, but everything downstream of extraction is source-agnostic.

---

## What the general skill would actually do

Given a customer's page cache plus their criteria exports:

1. **Extract** every prescription requirement per payer, verbatim, with a link back to source
2. **Map** each to an existing criteria, or flag it as a gap with a drafted definition
3. **Deduplicate** payers into the minimal set of documents that covers them
   *(J&B: 1,267 payer-documents → 580 distinct)*
4. **Produce** the payer × service-line matrix, the review queue, and the gap analysis
5. **Validate** with the 71 checks and report what failed

Steps 2 and 5 are where the value is, and both are already customer-agnostic — the mapping
rules and the validation rules are written as method, with the customer specifics isolated
in `JB_SPECIFIC_RULES.md`. That separation was worth keeping.

---

## Honest caveats

- **`extract.py` is gone.** Lost when `/private/tmp` was reaped. `rx_extracted.json` was
  rebuilt from `mapped_rows.json`, so the current outputs are intact, but the extractor
  itself would need rewriting for a general skill. It was the most customer-specific script
  anyway.
- **The mapping rules encode J&B's payer mix.** 144 rules tuned against incontinence,
  urological, ostomy, diabetic testing and wound care. A customer in a different product
  space would need rules added, not just constants changed.
- **The validation checks contain J&B probe cases** — Wisconsin's diagnosis routing, the
  Medicare SWO payers, the specific cache pages. Those would become per-customer fixtures.
