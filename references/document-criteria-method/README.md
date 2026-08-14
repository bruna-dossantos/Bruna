# Document Criteria — method

The **customer-neutral** half of the document-criteria work: how to read a payer's
prescription requirements, map them to canonical criteria, collapse payers into the minimum
set of documents, and prove the result. Nothing here names a customer.

The customer-specific half, and the working code, live in a sibling folder —
today that is `../J&B Document Criteria/`.

| File | |
|---|---|
| `CANONICAL_CRITERIA_MAPPING_RULES.md` | how to read a requirement and decide which criteria it maps to. 11 sections, each rule traceable to a real defect it prevents. |
| `MAPPING_VALIDATION_RULES.md` | the 71 checks, in 6 gates, and why each exists. Every check corresponds to a failure that actually happened. |
| `WHATS_REUSABLE.md` | which files and scripts are portable, which are customer data, and the seven constants that would have to become inputs. |

## Applying this to a new customer

Seven things are customer-specific. Everything else in the pipeline is generic:

1. path to the customer's page cache
2. paths to the criteria exports
3. output directory
4. which document-name patterns mean "this customer owns it"
5. which test / demo documents to exclude
6. **the supplier's own name, address and receiving phone/fax numbers** — needed so the
   contact-field guard works and the portable/customer split is computable
7. which criteria the reviewer has declared the survivor when several describe one concept

## What is NOT portable

- **The extractor.** It understands one wiki's HTML shape. A new source needs a new reader.
  Everything downstream of extraction is source-agnostic.
- **The 144 mapping rules** are tuned to incontinence, urological, ostomy, diabetic testing
  and wound care. A different product mix needs rules added, not constants changed.
- **The validation probe cases** — specific payers and pages — become per-customer fixtures.

## If this becomes a skill

Per the skill-authoring convention these files would move to
`~/Documents/Claude/skills/<skill-name>/`, one folder per skill. They are here for now
because the method is still being proven against a second customer.
