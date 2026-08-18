---
name: imaging-criteria-extractions
description: >
  End-to-end pipeline to turn an imaging/testing policy (Medicare LCD/NCD +
  companion article, or a payer CPB) into Tennr qualification criteria AND the
  extraction fields that evaluate them — order types, operational definitions for
  vague terms, UMLS-atom recall sets, a Tennr-format criteria doc/PDF, a coverage
  check, a click-through traceability HTML, a platform JSON with big code sets
  inlined, and a find→fix→re-check loop. Use when Bruna says "run the imaging
  criteria flow", "build imaging criteria and extractions", "generate extraction
  fields for this policy", or drops an imaging/testing LCD/policy. Imaging/testing
  (CT, MRI, DXA, molecular) — NOT DME/infusion.
---

# Imaging Criteria + Extractions — full pipeline

Turn a policy into criteria + extraction fields, then verify it. **Run the steps in
order.** Each step below maps to one script: what it's for, the command, its
inputs/outputs, and what must run before it. `close_loop.py` (Step 10) chains the
downstream steps and drives find → fix → re-check to convergence.

## Deliverables (what a full run produces, in `OUT/`)
- `<LCD>_rule_inventory.json/.md` — every policy rule, classified (Step 0)
- `<LCD>_criteria.json` — the criteria (human copy: code call-out, not the dump)
- `<LCD>_resolutions.json` + `<LCD>_resolver_report.md` — operational definitions
- `<LCD>_criteria_by_code.md/.docx/.pdf` — Tennr-format criteria doc (PDF = give to Tennr)
- `<LCD>_extraction_fields.csv` + `<LCD>_extraction_fields_by_code.md/.docx` — extraction fields
- `<LCD>_coverage_gaps.md` — criteria-vs-inventory gaps
- `<LCD>_traceability.html` — rule-first explorer (policy→rules→criteria)
- `<LCD>_criteria_explorer.html` — pathway-first explorer (pathway→criteria→click→policy; policy vs clinical split)
- `<LCD>_criteria.PLATFORM.json` + `<LCD>_group1_dx_codes.csv/.json/.txt` — evaluator copy w/ codes inlined
- `<LCD>_close_loop_report.md` — convergence report / worklist

## Run folder layout (how a finished run is organized — Step 11)
Generate flat into `OUT/`, then package with `organize_run.py` into ONE folder per
policy, named `<Theme> - <Payor> (<ID>)` — include the policy ID when there is one;
if not, use a more specific payor (plan / line of business) so runs can't collide:
```
MRI Head & Neck - Medicare (L37373)/
  README.md            ← START HERE: status + what a reviewer must confirm + file index
  1 - Policy Source/   ← source LCD / NCD / article PDFs
  2 - Working Files/   ← <LCD>_criteria.json, rule_inventory, rule_locations, traceability.json
  3 - Checks/          ← close_loop_report, resolutions, accepted_gaps, criteria.resolved, coverage, ambiguous_terms
  4 - Human Outputs/   ← criteria_by_code .docx/.pdf/.md, extraction_fields_by_code docs, traceability.html, criteria_explorer.html
  5 - Machine Outputs/ ← criteria.PLATFORM.json, MACHINE_full_codes.md, extraction_fields.csv, group1_dx_codes .csv/.json/.txt
```
`run_layout.py` is the single source of truth for the bucket a file lands in — keep
it in sync if you add an output. The cross-run **Summary & Decisions** doc stays one
level up (it spans all policies), not inside a run folder.

## Core principles (the decisions this encodes)
- **Order type = the qualification unit.** A code may have several; split when the
  criteria SET differs (stage/diagnosis/product/category), else keep as an OR inside
  one order type. (See [[order-types-model]].)
- **Operational definitions live in the criterion; recall synonyms live in the
  extraction fields; dictionary glosses are dropped.** ([[ambiguous-term-resolver]])
- **Code sets:** human doc = short call-out; **platform JSON = full literal set
  inlined** (the evaluator has no lookup), count-checksummed.
- **Generation is a loop, not one pass** — list rules first, cover them, check back,
  regenerate. The evaluator is strict + per-criterion + missing→FALSE, so criteria
  must be self-contained with explicit pass-throughs. ([[criteria-evaluator]])
- **Tennr left-side format** — write each criterion as a declarative requirement with
  explicit numbered AND/OR sub-items, never a run-on sentence:
  `The patient's medical records must document at least one of the following (1 or 2 or 3):`
  then `1. … 2. … 3. …` (use "all of the following" for AND). Write absolute exclusions
  as gates — `The patient does NOT have any of the following: 1. … 2. …` (evaluates TRUE
  when none present, so no extra pass-through). A criterion that only applies in some
  cases ends with a plain scoping sentence that doubles as the evaluator pass-through:
  `This requirement applies only when …; otherwise this criterion is considered met.`
  Always "patient" (never member/beneficiary); notes inline, never parenthetical.
  (See the `criteria-writer-imaging` quality-rules + [[criteria-evaluator]].)

## Setup (once)
- **API keys** present: `~/Claude/Projects/Credentials/umls_api_key.txt`
  and `BioPortal_API.txt`. ([[umls-term-glossing]])
- **venv** (for docx/pdf/pdfplumber steps): `python3 -m venv .venv && .venv/bin/pip
  install -r requirements.txt` (already created; gitignored).
- **Two interpreters** — matters per step:
  - `PY=python3` — stdlib steps + API steps (UMLS/BioPortal via stdlib `urllib`; no pip deps).
  - `PYV=.venv/bin/python` — needs python-docx / reportlab / pdfplumber (see `requirements.txt`).
- **Shared clients** in `criteria-toolkit/scripts/` (`umls_client.py`,
  `bioportal_client.py`, `expand_concepts.py`, `umls_synonyms.json`); skill scripts import them.
- Set `SRC` = extracted policy `.txt`s, `PDFS` = source PDFs, `CODES` = canonical dx CSV,
  `OUT` = `~/Claude/Projects/Criteria Updates/Imaging Vertical/<LCD> …/`.

## Interchange format — `criteria.json`
```
{ "policy": {lcd,title,payer,ncd_baseline,article, service_line?, plan_category?, doc_criteria:[...]},
  "groups": [{ "group_label", "codes": [{
     code, description, modality, contrast,
     "order_types": [{ order_type, context{stage,condition,product,category},
                       logic_expression, criteria: [{n,title,type,definition,source,
                       list_not_inlined?}] }] }]}]}
```
`service_line` / `plan_category` are optional doc-header labels — set them per policy
(they fall back to "Imaging / Radiology" and payer-or-MEDICARE), so the rendered doc is
labeled correctly for ANY policy, not just the one it was first built on.
`type` enum: CLINICAL_INDICATION | PRIOR_WORKUP | PRIOR_IMAGING | METHODOLOGY |
CONTRAST | THERAPY_LINKAGE | FREQUENCY | DOCUMENTATION | EXCLUSION | SPECIMEN.

---

## Step 0 — `extract_policy_rules.py` · make the rule-list FIRST
The completeness checklist: pulls every coverage rule from the policy text and tags
each `relevance` = clinical | administrative | out_of_scope, `type`, and `has_or_group`.
Nothing can be silently dropped once it's listed. **Run before authoring.**
```
$PY scripts/extract_policy_rules.py --policy $SRC/*.txt \
    --out-json $OUT/<LCD>_rule_inventory.json --out-md $OUT/<LCD>_rule_inventory.md
```
Out: rule inventory. Review the `.md`; only `clinical` rules drive coverage.

## Step 1 — criteria authoring (`criteria-writer` skill + the imaging prompt) → `criteria.json`
Invoke the `criteria-writer` skill with the **imaging prompt** as the generation
spec, the policy text, and the requested codes. **Feed the Step-0 inventory in and
require every clinical INDICATION/EXCLUSION/LIMITATION rule to be covered.** Inline
verbatim code lists; for a too-big set (e.g. 6,458 Group-1 codes) emit a call-out +
`list_not_inlined {what,count,location}` — never genericize. Assemble into
`criteria.json` (the interchange shape). Do NOT hand-write criteria.

## Step 2 — `build_order_types.py` · model the qualification unit
Wraps each code's criteria into `order_types`; if the policy forks a code (stage/
diagnosis/product/category) author separate entries; else one default order type
(AND of all criteria). Lints when one order type mixes lifecycle language (should split).
```
$PY scripts/build_order_types.py $OUT/<LCD>_criteria.json --out $OUT/<LCD>_criteria.json
```
In: Step-1 criteria. Out: criteria with `order_types`.

## Step 3 — `resolve_ambiguous_terms.py` · pin operational definitions
`detect` finds decisive-but-undefined terms per criterion (flags policy-defined
ones like "unusual duration = >2 weeks"). You author an operational definition (rule
+ positives/negatives + time_window + treatment + missing_data) per undefined term
in `resolutions.json`; `apply` embeds it inline; unresolved terms escalate.
```
$PY scripts/resolve_ambiguous_terms.py detect $OUT/<LCD>_criteria.json --out $OUT/<LCD>_terms.json
# author $OUT/<LCD>_resolutions.json for the NEEDS_OPERATIONAL_DEFINITION terms, then:
$PY scripts/resolve_ambiguous_terms.py apply $OUT/<LCD>_criteria.json \
   --resolutions $OUT/<LCD>_resolutions.json --out $OUT/<LCD>_criteria.resolved.json \
   --report $OUT/<LCD>_resolver_report.md
```
Runs AFTER Step 2. `criteria.resolved.json` becomes the criteria fed downstream.
(Step 10 applies resolutions for you; you still author `resolutions.json`.)

## Step 4 — render the criteria doc — `render_criteria_doc.py` / `render_criteria_docx.py` / `render_criteria_pdf.py`
The human criteria document in three formats; `.pdf` is the artifact to hand Tennr.
```
$PY  scripts/render_criteria_doc.py  $OUT/<LCD>_criteria.resolved.json > $OUT/<LCD>_criteria_by_code.md
$PYV scripts/render_criteria_docx.py $OUT/<LCD>_criteria.resolved.json --out $OUT/<LCD>_criteria_by_code.docx
$PYV scripts/render_criteria_pdf.py  $OUT/<LCD>_criteria.resolved.json --out $OUT/<LCD>_criteria_by_code.pdf
```
docx/pdf need `$PYV`. Tennr house format: banners, □ checklist, policy-quote callouts, appendix.

## Step 5 — `build_extraction_fields.py` · extraction fields (UMLS atoms)
Per criterion: detects clinical concepts (BioPortal annotator), builds each field's
recall set from **UMLS atoms** (+ ICD from atoms), writes a "represented in a
variety of ways: …" directive. Needs `requests` → `$PY`.
```
$PY scripts/build_extraction_fields.py $OUT/<LCD>_criteria.resolved.json --out $OUT/<LCD>_extraction_fields.csv
```
Helper — `expand_concepts.py` (shared): `validate` grounds model-proposed related
concepts; `atoms` builds a synonym set; `test` gates recall/precision on labeled charts.

## Step 6 — `render_extractions_doc.py` · companion doc
Mirrors the criteria doc on the extraction side (code→order type→criterion→fields).
```
$PYV scripts/render_extractions_doc.py $OUT/<LCD>_extraction_fields.csv \
    --out-md $OUT/<LCD>_extraction_fields_by_code.md --out-docx $OUT/<LCD>_extraction_fields_by_code.docx
```

## Step 7 — `coverage_check.py` · close the completeness check
Diffs criteria against the Step-0 inventory; ranks least-covered rules by type.
```
$PY scripts/coverage_check.py $OUT/<LCD>_criteria.resolved.json --inventory $OUT/<LCD>_rule_inventory.json \
    --out $OUT/<LCD>_coverage_gaps.md --threshold 0.4
```

## Step 8 — traceability — `build_traceability.py` → `locate_rules_in_pdf.py` → HTML renderers
Two self-contained explorers (PDFs base64-embedded; internet once for the PDF.js CDN):
- **Rule-first** (`render_traceability_html.py`): click a rule → jump/highlight in the
  PDF; overlay all rules by type; chips count clinical coverage only (admin/out-of-scope
  behind a toggle). Best for "did we capture every rule?"
- **Pathway-first** (`render_criteria_explorer.py`): each ORDER TYPE is a collapsible
  section of its criteria; click a criterion → jump to where it came from in the policy.
  Each criterion visibly separates **📄 Policy** (blue) from **🩺 Clinical interpretation**
  (amber, reviewer PENDING). Best for "walk the pathways / show me the source of a rule."
  Criterion→policy link comes from the traceability `became` map (falls back title-wise
  so identical criteria across codes all link).
```
$PY  scripts/build_traceability.py $OUT/<LCD>_rule_inventory.json $OUT/<LCD>_criteria.resolved.json --out $OUT/<LCD>_traceability.json
$PYV scripts/locate_rules_in_pdf.py $OUT/<LCD>_rule_inventory.json --pdf $PDFS --out $OUT/<LCD>_rule_locations.json
$PY  scripts/render_traceability_html.py $OUT/<LCD>_traceability.json --locations $OUT/<LCD>_rule_locations.json \
     --pdf $PDFS --title "<LCD>" --out $OUT/<LCD>_traceability.html
$PY  scripts/render_criteria_explorer.py $OUT/<LCD>_criteria.resolved.json --traceability $OUT/<LCD>_traceability.json \
     --locations $OUT/<LCD>_rule_locations.json --pdf $PDFS --title "<LCD>" --out $OUT/<LCD>_criteria_explorer.html
```
`locate` needs pdfplumber (`$PYV`). Order: build → locate → render (both HTMLs).
**Policy vs clinical context:** `criterion_view.py` splits each criterion back into the
policy requirement vs the operational-definition prose the resolver folded inline — the
docx/pdf and the explorer all use it so the two never read as one blob.

## Step 9 — `build_machine_copy.py` · platform JSON + code files
Emits the evaluator copy: the full literal code set inlined in EVERY covered-dx
criterion (count-checksummed, aborts on mismatch); human `criteria.json` keeps the
call-out. Also a readable machine `.md` + paste-ready codes `.txt`.
```
$PY scripts/build_machine_copy.py $OUT/<LCD>_criteria.resolved.json --codes $CODES --out-dir $OUT
```

## Step 10 — `close_loop.py` · find → fix → re-check (the orchestrator)
Applies resolutions, checks undefined terms + uncovered **clinical** rules, and
**converges** (or emits a worklist of what still needs authoring). With `--render`
it re-runs Steps 4–9 so nothing drifts. Reviewed residuals (out-of-scope/matcher-miss)
go in `accepted_gaps.json` with a reason so heuristic noise can't block convergence.
Authoring stays model/human-in-the-loop by design.
```
$PY scripts/close_loop.py $OUT/<LCD>_criteria.json --inventory $OUT/<LCD>_rule_inventory.json \
    --resolutions $OUT/<LCD>_resolutions.json --codes $CODES --accepted-gaps $OUT/<LCD>_accepted_gaps.json \
    --out-dir $OUT --pyv $PYV --pdfs $PDFS --render
```
**The loop (manual):** run → read the worklist → author new operational definitions /
re-author gap criteria / accept a reviewed residual → re-run → repeat until
"Converged: YES".

### Step 10b — Autonomous mode (agent-driven, best-effort, always finishes)
When asked to "run the loop automatically / until it feels good," the agent drives the
loop itself and always ends with a fully rendered package:
1. **Check** — run Step 10 *without* `--best-effort` to get the current worklist.
2. **Author** — for every undefined decisive term, write a real operational definition
   into `resolutions.json`; for every uncovered clinical rule, author a gap criterion
   (or add it to `accepted_gaps.json` with a reason if genuinely out-of-scope). All
   authored items carry `reviewer: PENDING`.
3. **Re-check** — re-run and repeat 2–3 until the worklist is empty, or until further
   passes stop shrinking it (a couple of passes).
4. **Always finish** — do a final run with `--best-effort`. Anything still unresolved is
   **auto-stubbed** (a loud `⚠ AUTO-STUB … PENDING — REQUIRED` definition, treated as
   NOT met) or **auto-accepted**, the full package is rendered, and everything
   auto-handled is listed under **“⚠ NEEDS REVIEW”** in the report. So you always get a
   complete, in-sync package plus an explicit list of what a reviewer must still confirm.
```
$PY scripts/close_loop.py $OUT/<LCD>_criteria.json --inventory $OUT/<LCD>_rule_inventory.json \
    --resolutions $OUT/<LCD>_resolutions.json --codes $CODES --accepted-gaps $OUT/<LCD>_accepted_gaps.json \
    --out-dir $OUT --pyv $PYV --pdfs $PDFS --best-effort
```
`--best-effort` implies render (it always writes the full downstream). The auto-stubs
never invent clinical meaning — they mark the term as unmet + PENDING so it can't
silently pass; the agent's job across re-runs is to replace them with real definitions.

## Step 11 — `organize_run.py` · package the run into one named folder
Last step. Sorts the flat `OUT/` into the run-folder layout above and writes the
`README.md` (START HERE) from the close-loop status. Non-destructive; idempotent;
leaves unrecognized / superseded files (`older - …`, `~$…`) at the root and lists
them under "Unsorted".
```
$PY scripts/organize_run.py $OUT --theme "MRI Head & Neck" --payor "Medicare" --policy-id L37373
# or sort inside an existing run folder:  … $RUNDIR --theme … --payor … --in-place
# to reverse before re-generating:        $PY scripts/organize_run.py $RUNDIR --flatten
```
Or fold it into the loop's final pass: add `--organize --theme "…" --payor "…"
[--policy-id …]` to the `close_loop.py … --best-effort` call and it packages after
rendering. **Re-generating an organized run:** `--flatten` first, re-run, re-organize.

## Dependency order (what must precede what)
Step 0 → 1 → 2 → 3 → (4,5,6,7,8,9 in any order) → 10 wraps them → 11 packages. Step 8
render needs `locate` first. Step 9 & the PLATFORM copy need `$CODES`. Steps 5/8-locate
hit the APIs/PDFs; the rest are offline. Run Step 11 (or `--organize`) only at the very
end — once organized, `--flatten` before any re-generation.

## Interpreter cheatsheet
`$PYV` (venv): render_criteria_docx, render_criteria_pdf, render_extractions_doc,
locate_rules_in_pdf. `$PY` (system, has requests): everything else, incl.
build_extraction_fields (BioPortal/UMLS) and close_loop (which shells `$PYV` for the
lib steps via `--pyv`).

## Constraints & honest limits
- Criteria text + operational definitions are model-authored — every one flags
  "reviewer: PENDING"; a clinician signs off before go-live.
- Coverage/relevance/locate are heuristics (token overlap, lexicon, term-match) —
  they flag candidates; accept reviewed residuals rather than chase 100%.
- UMLS atoms are exact synonyms of the bare term's CUI — seed on the context-qualified
  term for scoped concepts. ICD `bioportal_fuzzy_review` rows are review-tier.
- Real accuracy needs real charts with outcomes (SimonMed) — not built.

See also: [[imaging-ontology-expansion]], [[order-types-model]],
[[ambiguous-term-resolver]], [[criteria-evaluator]], [[umls-term-glossing]].
