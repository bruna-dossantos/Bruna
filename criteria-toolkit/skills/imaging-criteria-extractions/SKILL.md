---
name: imaging-criteria-extractions
description: >
  Generate imaging/testing qualification criteria from a policy AND the matching
  extraction fields Tennr needs to evaluate them — the gap the criteria-writer
  skill leaves ("Tennr auto-generates extraction fields downstream"). Runs the
  four-step flow: (1) write criteria with the imaging prompt + criteria-writer,
  (2) render a "Qualification Criteria by Code" doc, (3) detect the clinical
  concepts in each criterion via the BioPortal/UMLS ontology APIs, (4) emit a
  per-criterion extraction-fields CSV, then enrich the illustrative rows with
  model-proposed, ontology-validated concept sets. Use when Bruna says "build
  imaging criteria and extractions", "generate extraction fields for this
  policy", "what extractions does this criteria need", "run the imaging
  criteria flow", or drops an imaging/testing LCD/policy and wants criteria +
  extraction fields. Imaging/testing (CT, MRI, DXA, molecular) — not DME/infusion.
---

# Imaging Criteria + Extraction Fields

Two things ship together here: the **criteria** (the clinical requirements, left
side) and the **extraction fields** (the recall-only "go find" directives that
pull evidence from the chart). The `criteria-writer` skill deliberately writes
criteria only — Tennr auto-generates extraction fields downstream — and for
imaging that auto-generation is the weak link, because illustrative lists
("suspected spinal infection or malignancy", "such as motor weakness…") need to
be broadened so the chart's real phrasing (spondylodiscitis, epidural abscess)
still matches. This skill produces both and makes the broadening explicit,
reviewable, and testable.

## Core principle

**The generation model decides a list is illustrative** (not a pre-pass). When it
does, the ontology expansion goes into the **extraction field** — a flat recall
set, no embedded reasoning — never into the criterion prose. The criterion stays
clean; recall lives one layer down. This fits the platform constraint that
extraction fields are simple "go find" directives.

Ontology is a **validator, not a generator**: raw ontology search underdelivers
(it returns rare edge concepts and misses the common ones). The model proposes
the clinical realizations; the ontology confirms each is real and attaches codes.

## Inputs

- An imaging/testing policy (Medicare LCD/NCD + companion article, or a payer CPB)
  — text or PDF.
- The requested HCPCS/CPT codes.
- Payer / plan-category / state context.
- The imaging prompt (`Imaging_Testing_prompt_SHIP_NOW.md`, or `_REVISED.md` once
  the schema fields land).

## Prereqs

- API keys present: `~/Documents/Claude/Projects/Credentials/BioPortal_API.txt`
  and `umls_api_key.txt`. See [[umls-term-glossing]].
- Shared clients live in `criteria-toolkit/scripts/`
  (`bioportal_client.py`, `umls_client.py`, `expand_concepts.py`); the skill
  scripts import them.

## Interchange format — `criteria.json`

Every step reads/writes this shape (see `examples/L37373_70450.criteria.json`):

```json
{
  "policy": {"lcd","title","payer","ncd_baseline","article"},
  "groups": [{
    "group_label": "CT Scans — Group 1",
    "codes": [{
      "code","description","modality","contrast",
      "order_types": [{                    // the qualification unit; a code may have several
        "order_type": "Initial: Rheumatoid Arthritis",
        "context": {"stage","condition","product","category"},
        "logic_expression": "C1 AND (C2 OR C3) AND C4",   // AND/OR within THIS order type
        "criteria": [{
          "n": 1,
          "title": "Headache / Dizziness Pathway",
          "type": "CLINICAL_INDICATION",   // enum: CLINICAL_INDICATION | PRIOR_WORKUP |
                                           // PRIOR_IMAGING | METHODOLOGY | CONTRAST |
                                           // THERAPY_LINKAGE | FREQUENCY | DOCUMENTATION |
                                           // EXCLUSION | SPECIMEN
          "definition": "verbatim criterion text",
          "source": "LCD L37373, CT sections D and E"
        }]
      }]
      // a code with a flat top-level "criteria" list is treated as one order type
    }]
  }]
}
```

## The flow

This is a **loop, not a single pass** — the fix for criteria generation flattening
pathways and dropping safety rules. List every rule first (Step 0), generate
covering that list, then check back against it (Step 6) and regenerate what's
missing.

### Step 0 — Make the rule list first (completeness fix)

```bash
python3 scripts/extract_policy_rules.py --policy lcd.txt ncd.txt article.txt \
    --out-json rule_inventory.json --out-md rule_inventory.md
```

Before any criteria are written, enumerate every rule the policy states —
classified INDICATION / EXCLUSION / LIMITATION / ADMINISTRATIVE, with `has_or_group`
flagging alternative routes (pathways). This is the checklist nothing can be
silently dropped from. Review/curate the `.md`; the agent may add rules the
deterministic pass missed.

### Step 1 — Write the criteria (cover every rule)

Invoke the `criteria-writer` skill with the imaging prompt, the policy text, and
the requested codes. **Feed the rule inventory in and require every INDICATION,
EXCLUSION and LIMITATION rule to be covered.** Decide order-type structure here:
if the policy forks a code's criteria by lifecycle stage / diagnosis / product /
category, author each as a separate `order_type` (Step 2); if routes only differ in
how one requirement is met, keep them as an OR inside one order type. Never flatten
a genuine split into a single AND-list. Do NOT hand-write criteria — always go
through `criteria-writer`.

### Step 2 — Model order types (the qualification unit)

```bash
python3 scripts/build_order_types.py criteria.json --out criteria.with_order_types.json
```

The unit is the **order type**: one code + payer/context with its OWN criteria set.
A code can have several. Two levels:
- **Split into separate order types** when the criteria SET differs — by lifecycle
  stage (Initial/Continuation/Renewal/Recert/Replacement), diagnosis, product, or
  clinical category (e.g. J1745: Initial-RA vs Continuation-RA). Author these as
  separate entries in `order_types`. See `examples/J1745_infliximab_multi_order_type.*`.
- **Keep in ONE order type (OR inside its `logic_expression`)** when the alternative
  routes share the same documentation + medical-necessity rules (e.g. lumbar MRI:
  red-flag route OR failed-conservative route → `C1 AND (C2 OR (C3 AND C4)) AND C5`).
  See `examples/lumbar_MRI_one_order_type.*`.

If a code only has a flat `criteria` list, it's wrapped into one default order type
(AND of all criteria) — correct for diagnostic imaging, where a CPT code is usually
one order type. The script also **lints**: it flags an order type whose criteria mix
lifecycle language (both "initial" and "continuation") — a sign it should be split.

### Step 3 — Render the criteria doc

```bash
python3 scripts/render_criteria_doc.py criteria.with_order_types.json > <LCD>_criteria_by_code.md
```

Renders each code's order types as separate qualification units, each with its own
criteria and `logic_expression`. For a .docx hand-off, run through the `docx` skill.

### Step 4 — Build the extraction fields (UMLS atoms)

```bash
python3 scripts/build_extraction_fields.py criteria.with_order_types.json --out extraction_fields.csv
```

Per criterion: detects clinical concepts (BioPortal Annotator, clinical semantic
types), then builds each field's recall set from **UMLS atoms** — the authoritative
synonym strings for that concept's CUI — and pulls ICD-10 codes straight from the
concept's ICD atoms (falling back to a guarded BioPortal search when the CUI has
no ICD atom). The directive names every representation, e.g. *"Find documentation
of Dizziness… represented in a variety of ways: dizziness, vertigo, …, etc."*
Each concept also gets a **UMLS definition** (from its CUI — NCI/MeSH/MedlinePlus)
to enrich the field for reviewers and the evaluator; use `--plain` upstream for
patient-friendly text. (UMLS is the right source for definitions — the NCBI
E-utilities/MedGen APIs are for literature/genetics, narrower and redundant here.)
Columns: `code, modality, order_type, criterion_n, criterion_type, criterion_title,
extraction_field, directive, seed_term, ontology, grounded_label, class_id, cui,
concept_set, definition, definition_source, icd10_candidates, icd_source,
needs_review, source_criterion`.

### Step 5 (optional) — Add related concepts / gate on charts (Way 1)

Atoms give exact synonyms of a concept, not *related* concepts. When a policy's
illustrative list needs broader recall (e.g. "intracranial bleeding" → subdural,
subarachnoid, epidural hematoma — distinct CUIs), the model proposes them and
`expand_concepts.py validate` grounds them. Seed atoms on the **context-qualified**
term ("intracranial hemorrhage"), not the bare surface ("bleeding"), or the atoms
resolve to the generic concept and lose context. Gate on real charts with
`expand_concepts.py test` when SimonMed-style labeled charts are available.

### Step 6 — Coverage completeness check (close the loop)

```bash
python3 scripts/coverage_check.py criteria.json --inventory rule_inventory.json --out coverage_gaps.md
```

Diffs the criteria against the Step-0 rule inventory and ranks the least-covered
rules, grouped by type, with the missing terms — catches dropped branches (this is
how the L37373 pacemaker / "not a suitable MRI candidate" indication surfaces at
25%). **Any clinical rule below threshold feeds back to Step 1 for a targeted
second pass.** Loop until no clinical rule is uncovered. (Can also diff against raw
policy text with `--policy` instead of `--inventory`.) A low score can be a real
gap or an intentionally-omitted administrative requirement — the type tag helps
you tell fast.

## Outputs

- `rule_inventory.md` / `.json` — the policy's full rule list (Step 0 checklist).
- `<LCD>_criteria_by_code.md` — criteria doc, order types per code with logic.
- `extraction_fields.csv` — per-criterion extraction fields, atom-based recall sets + ICD.
- `coverage_gaps.md` — completeness gap report (criteria vs the rule inventory).

Save deliverables under `Documents/Claude/Projects/Criteria Updates/Imaging Vertical/`.

## Constraints & honest limits

- `concept_set` is a flat recall list — no reasoning — so it fits the current
  extraction-field model without a schema change. It is a **distinct output
  surface** from the criteria prompt.
- **Atoms lose context**: a bare surface ("bleeding") resolves to the generic CUI
  (Hemorrhage → R58), not the intracranial concept. Seed atoms on the
  context-qualified term (step 5) for those.
- The detector over-generalizes some terms ("focal problem" → "Problem") and
  over-detects (verbs, anatomy); those rows are for review.
- ICD-10 candidates are review-tier. `icd_source=umls_atoms` is authoritative for
  the concept; `bioportal_fuzzy_review` still lets off-target codes through.
- Coverage check is a heuristic (token overlap); it flags candidates, doesn't
  decide correctness. Real recall needs real charts with outcomes.

See [[imaging-ontology-expansion]] for the design rationale and recall evidence.
