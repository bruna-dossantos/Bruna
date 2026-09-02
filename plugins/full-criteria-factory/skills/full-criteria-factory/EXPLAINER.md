# Full Criteria Factory

_How the skill works — written so anyone can follow the top half, and an engineer can run it from
the bottom half. No prior knowledge needed._

---

## The idea, in plain terms

Insurance payers publish long documents that say when a medical test or scan is covered — for
Medicare these are called LCDs, plus a companion billing article; commercial payers publish their
own medical policies. Today a person reads each of those documents by hand and turns it into the
rules Tennr uses to decide "does this patient qualify?"

The Full Criteria Factory does that conversion automatically. You give it a policy; it produces a
clean **qualification checklist** in two forms:

- a **document a human reads and signs off** (a PDF), and
- a **file the Tennr platform runs** (JSON) to auto-check a patient's records.

Think of it as an assembly line: a rulebook goes in one end, and a reviewed, machine-runnable
checklist comes out the other. The same line runs for one policy or for hundreds.

**Why it matters:** it turns days of manual policy reading into a first draft in minutes, keeps
every rule traceable back to the exact line in the source policy, and produces the structured file
the platform needs — so criteria go live faster and with fewer misses. Everything it makes is a
**draft that a clinician approves** before it's used; the factory does the heavy lifting, a human
makes the final call.

---

## What goes in, what comes out

**In:**
1. The policy PDFs — the LCD, any national NCD, and the billing/coding article. (They're placed on
   disk by hand because CMS blocks automated downloads.)
2. The covered diagnosis codes — the ICD-10 codes the policy says support medical necessity.
3. The billing codes (CPT/HCPCS) you want criteria for.

**Out** (one tidy folder per policy):
- The criteria as **PDF / Word / Markdown** — the human-readable checklist. The PDF is what you
  hand to a reviewer or a customer.
- **`_tennr_order_types.json`** — the file the Tennr platform ingests.
- The **platform copy** (`_criteria.PLATFORM.json`) with every diagnosis code baked in — what the
  evaluator actually runs.
- Two **click-through web pages** for review (explained below).
- The **review worklists** (which items still need a human eye).
- A **README** that says "start here" and what's left to confirm.

---

## How it works — the twelve steps

The line has twelve steps. They fall into five easy beats: **understand → write → produce →
check → package.** Each step below gives the plain purpose first, then the script an engineer
runs, in parentheses.

### Understand the policy
**0. List every rule.** Read the whole policy and write down every coverage rule it contains,
labeling each as clinical, administrative, or out-of-scope. This becomes the master checklist, so
nothing can quietly fall through later. _(`extract_policy_rules.py`)_

### Write the criteria
**1. Draft the criteria.** An AI turns those rules into a plain checklist — one set per billing
code — in Tennr's house style (numbered "the record must document at least one of…" lists, and
exclusions written as "the patient does NOT have…" gates). It's required to cover every clinical
rule from Step 0. _(the `criteria-writer` skill with the imaging prompt)_

**2. Model the order types.** Group each code's criteria into **order types** — the actual unit
that gets qualified. When a single code covers genuinely different clinical situations (say, a DVT
work-up versus pre-surgery vein mapping), it becomes several order types; otherwise it stays one.
_(`build_order_types.py`)_

**3. Pin down the vague words.** Policies lean on fuzzy words like "recent" or "suspected." This
step writes an exact, operational meaning for each decisive vague term directly into the criterion,
so the evaluator never has to guess. _(`resolve_ambiguous_terms.py`)_

### Produce the outputs
**4. Render the criteria document.** Produce the human-readable checklist in Markdown, Word, and
PDF. The **PDF is the artifact you hand to people.** _(`render_criteria_doc.py` / `_docx` / `_pdf`)_

**5. Build the extraction fields.** For every criterion, write the "**go get and find**"
instructions that locate the raw facts in a patient's chart — for example, "find the ankle-brachial
index value." There's a firm rule here: an extraction field may only *fetch* data. It carries no
thresholds, no judgment words, and no "if/when" logic — all of that stays in the criterion. Two
companions run alongside: a script that sorts every term into an **accept/reject worklist**
(`build_extraction_review.py`), and the one that assembles the **platform-ingest JSON**
(`build_tennr_order_type_json.py`). _(A dictionary-based fallback, `build_extraction_fields.py`,
can auto-detect concepts to seed recall, but the AI-authored fields are what ship — see "Where the
words come from" below.)_

**6. Render the extractions document.** A companion doc that mirrors the criteria doc on the
extraction side, so a reviewer can see each code → criterion → the fields that feed it.
_(`render_extractions_doc.py`)_

**7. Coverage check.** Compare the finished criteria back against the Step-0 rule list and flag
anything left uncovered. This is the completeness safety net. _(`coverage_check.py`)_

**8. Traceability explorers.** Build two self-contained web pages that let a reviewer audit the
work in minutes instead of hours:
- the **traceability view** starts from a policy rule and jumps to that exact spot in the source
  PDF — proof that nothing was missed or invented; and
- the **explorer view** starts from a criterion and shows where it came from, color-separating
  "straight from the policy" text from "our clinical interpretation."
_(`build_traceability.py` → `locate_rules_in_pdf.py` → the HTML renderers)_

**9. Machine copy.** Produce the evaluator's copy with the **full diagnosis code set inlined** into
every covered-diagnosis criterion. It's count-checksummed, so the build stops rather than ship a
mismatched code list. _(`build_machine_copy.py`)_

### Check and package
**10. Find → fix → re-check (the orchestrator).** This is the brain of the line. It applies the
operational definitions, checks for any undefined terms or uncovered clinical rules, and either
declares the policy **converged** (clean) or hands back a short worklist of what still needs
authoring. In best-effort mode it always finishes a complete package and lists anything it had to
auto-handle under a clear "NEEDS REVIEW" heading. It also re-runs steps 4–9 so nothing drifts out of
sync. _(`close_loop.py`)_

**11. Package the run.** Sort everything into **one named folder per policy** with a START-HERE
README and numbered buckets: `1 Policy Source`, `2 Working Files`, `3 Checks`, `4 Human Outputs`,
`5 Machine Outputs`. _(`organize_run.py`)_

---

## Where the words come from — the term library

Each extraction field carries a **recall set**: the "may be recorded as: X, Y, Z…" list of every
way a concept can appear in a chart. That list is the difference between catching a diagnosis and
missing it because the doctor phrased it differently. It's built from two sources.

**1. The AI's own medical knowledge (today's default).** When the factory writes a field, the AI
draws the synonyms from its clinical training — for "stenosis" it offers narrowing, occlusion, and
so on. This reads naturally and is fast, but the terms are the model's own; on their own they
aren't guaranteed to be real, coded medical concepts.

**2. The medical dictionaries — UMLS and BioPortal (the grounding engine).** This is where the
terms get validated against authoritative sources:
- **BioPortal's Annotator** scans the criterion text and automatically detects the medical concepts
  in it (matching them against standard vocabularies like SNOMED and NCIT).
- **UMLS** — the U.S. National Library of Medicine's *Unified Medical Language System* — is a giant
  thesaurus that merges 200-plus coding systems (SNOMED, ICD-10, MeSH, NCIT, and more) into single
  unified concepts. For each concept it returns the **"atoms"**: every recorded label and spelling
  for that one concept across all of those systems. That's the authoritative synonym list, and it
  also yields the concept's ICD-10 codes.

So an "atom" is simply *one of the many official ways a single medical concept is written down.*

**How the two combine.** Every candidate term is checked against UMLS and sorted into three
buckets: **grounded** (it resolves to a real UMLS concept — trust it), **fuzzy** (only a loose
match — verify it), and **not found** (drop or flag it). That bucketing is the extraction
review worklist. The pattern that works best is *the AI proposes the synonyms and UMLS confirms
which are real* — because a raw dictionary search alone surfaces rare edge terms and misses the
common phrasings, while the AI alone can occasionally invent a plausible-but-wrong one.

**The honest limit.** Right now the synonyms that ship are mostly AI-authored, with the UMLS
grounding running as the validator and fallback (it needs live API access). Truly measuring how
well the term library catches concepts in real charts requires testing against real documents with
known outcomes — that final gate isn't built yet.

---

## Running it at scale — batch mode and the review layers

**Batch mode** runs the entire line across many policies in small parallel waves. For each policy
it goes **Author → QA → Summary**: one AI drafts the package, a second, independent AI acts as a
skeptic and tries to poke holes, and a third rolls everything up into a dashboard that flags which
policies to review first. _(`batch/imaging_criteria_batch.workflow.js`)_

On top of the base line, a set of optional **review workflows** add rigor once drafts exist:
- **SME accept pass** — an AI acting as a clinical expert reviews every operational definition and
  auto-accepted gap, and flags any detail that really belongs *inside* a criterion.
- **QA backfill** — re-runs the independent QA for any policy whose check failed, and refreshes the
  dashboard.
- **Split order types** — breaks a bundled order type into one per clinical pathway when the
  branches carry different prerequisites.
- **Author / fill extraction fields** — write the retrieval-only finder fields, or fill in specific
  gaps left behind.
- **Author deferred codes / apply SME** — add codes the policy covers that weren't in the original
  list, or fold the SME's decisions back into the criteria.

---

## For engineers — how to actually run it

`SKILL.md` in this folder is the authoritative, command-by-command runbook; this doc is the
orientation. The essentials:

- **Two Python interpreters.** `python3` for the stdlib and API steps (UMLS/BioPortal, coverage,
  close-loop); the local `.venv/bin/python` for the steps that need `python-docx`, `reportlab`, or
  `pdfplumber` (the Word/PDF renders and PDF locate). `close_loop.py` shells the venv for you via
  `--pyv`.
- **Dependency order.** Step 0 → 1 → 2 → 3 → (4–9 in any order) → 10 wraps them → 11 packages.
  Step 8's HTML render needs `locate_rules_in_pdf.py` to run first; steps 5 and 8-locate hit the
  external APIs/PDFs, the rest are offline.
- **One-policy fast path.** `close_loop.py … --best-effort --organize` runs the whole downstream to
  a finished, packaged run folder and never half-fails.
- **Keys.** UMLS and BioPortal API keys live in `~/Claude/Projects/Credentials/`. Source PDFs must
  be staged on disk (CMS blocks automated fetch).
- **The hard rules the code enforces.** Extraction fields are retrieval-only (no thresholds/
  judgment/conditionals); the machine copy count-checksums the code set and aborts on mismatch;
  extraction-field tags must come from the platform's fixed vocabulary; every criterion ships
  `reviewer: PENDING`.

---

## The vocabulary (worth knowing on both teams)
- **Order type** — the unit of qualification: a billing code + payer + its own set of criteria.
- **Operational definition** — an exact, testable meaning pinned to a vague policy word, written
  into the criterion itself.
- **Criteria judge; extraction fetches** — the criterion holds all the logic and thresholds; an
  extraction field only locates the raw value in the chart.
- **Reviewer PENDING** — the label on everything until a clinician signs off; the final human gate.

## The honest limits
- The criteria and definitions are AI-drafted first passes — a clinician must review and sign off.
- Coverage and traceability are heuristics: they flag candidates, not certainties.
- The criteria-authoring rules are tuned and validated for **imaging/testing** today (CT, MRI, DXA,
  ultrasound, vascular, molecular). DME and infusion have their own criteria-writer skills.
