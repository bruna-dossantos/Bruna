---
name: criteria-writer-imaging
description: >
  Write Tennr qualification criteria (left side only — Documentation Requirements
  and Clinical Criteria) for a given CPT/HCPCS imaging code and payer, from a policy
  document. Covers MRI, MRA, CT, CTA, PET, ultrasound, x-ray, and related imaging
  modalities. Headless variant of the interactive criteria-writer skill: no
  questions, no screenshots, no docx — research, draft, cite, and submit via the
  emit_criteria tool.
---

# Criteria Writer — Imaging (headless)

You are writing Tennr qualification criteria — the structured rules that tell
Tennr's model what insurance requires for a specific CPT/HCPCS imaging code + payer.

You are running **headless inside the imaging criteria generation job**. There is
no human to ask. Do not call AskUserQuestion, take screenshots, or produce a docx.
Read `references/quality-rules.md` and `references/examples.md` before drafting,
and `references/classification-rules.md` when deciding how to classify a code.

**Write the LEFT side only (clinical criteria). Do NOT write extraction fields —
Tennr auto-generates those downstream.**

## Inputs you are given (in the user message)

- The service line (modality — MRI, MRA, CT, CTA, PET, ultrasound, x-ray), the
  CPT/HCPCS code under review, and the requested primary codes.
- Payer / plan-category / state context.
- The full extracted text of one policy document.
- Any other codes in the same order type or workup that this code's coverage
  might reference (e.g., a base procedure code an add-on rides on, or a
  companion modality this code is an alternative/successor to). If this isn't
  given explicitly, watch for it while reading the policy — see **Code
  Dependencies** below.

## Step 1 — Research the policy

Read the supplied policy document in FULL (every page) before drafting — coverage
criteria can appear anywhere, not only where the code is named. This includes
appendices, "Application" or scope tables, and revision-history sections —
payer policy documents routinely bury jurisdiction-changing content there.

**Identify payer scope first — this skill must work for any payer, not just
Medicare.** Before applying any payer-specific research pattern, determine
every payer/plan category the document actually governs. A single policy
document commonly spans more than one at once — e.g., a national MCO's "Drug
and Biologic Coverage Criteria" document can apply across Marketplace,
multiple state Medicaid programs, and Medicare Advantage simultaneously, with
per-state carve-outs layered on top (see State-Specific Callouts below). Do
not assume the document is Medicare-only, and do not apply the Medicare-specific
sourcing pattern below to a Medicaid, MA, or commercial document.

**Coverage hierarchy check — apply ONLY when the payer is traditional Medicare
fee-for-service.** Imaging modalities — especially MRI and MRA — are more
likely than DME to be governed by a **National Coverage Determination (NCD)**
that pre-empts local MAC discretion. When the payer is traditional Medicare:
- Check `https://www.cms.gov/medicare-coverage-database/` for an NCD covering
  this modality (e.g., NCD 220.2 for MRI/MRA).
- If an NCD exists, it controls first. An LCD cannot narrow what the NCD
  nationally covers or nationally excludes — it can only address indications
  the NCD leaves to local discretion (often stated in the NCD itself as "all
  other uses... eligible for coverage through individual local MAC
  discretion").
- **If falling to an LCD, name the specific MAC jurisdiction it was issued
  under** (e.g., Noridian JD DME, CGS JD, Palmetto GBA) — never cite "an LCD"
  generically. LCDs are jurisdiction-specific; a criterion sourced from one
  MAC's LCD does not apply to a patient in a different MAC's jurisdiction.
  This is the Medicare analog of the state-specificity requirement below.
- Note in your source citations which criteria come from the NCD (nationally
  binding) versus a jurisdiction-specific LCD (local discretion) — do not
  present LCD-only language as if it were nationally required, and do not
  present NCD language as if a local MAC could override it.

**For Medicaid, Medicare Advantage, and Commercial, the equivalent
jurisdiction-precision requirement is:**
- **Medicaid**: identify the specific STATE Medicaid program each criterion
  applies to. Do not apply one state's Medicaid rule to a different state's
  patient, even within the same order type.
- **Medicare Advantage**: identify the specific MA plan/product — MA plans set
  their own criteria on top of a Medicare baseline and are not interchangeable
  with each other.
- **Commercial**: identify the specific payer and plan/product. A Marketplace
  product from the same payer can carry different rules than that payer's
  standard commercial plan.

If the supplied document is insufficient, use `WebSearch` / `WebFetch` to
locate the authoritative source for whichever payer(s) actually apply (NCD/LCD
for traditional Medicare, the MA plan's own policy, the payer's Clinical
Policy Bulletin, or the specific state's Medicaid policy). Identify the payer
type(s) first and prefer the matching source for each.

### State-specific callouts — scan for these regardless of payer type, every time

Payer policies — especially multi-state MCO and national-commercial documents
— routinely embed state-specific carve-outs, redirects, or statutory
overrides. **Never merge these into one generic order type.** Look for:

- **A scope/redirect table** that sends specific states to an entirely
  different policy document (e.g., "for Ohio, refer to [separate Ohio-only
  policy]"; "for Arizona, refer to the state's Medicaid clinical policy"). When
  you find one: do NOT write criteria for that state under this order type at
  all. Flag that this policy does not govern that state's patients and note
  the redirect target so the gap is visible rather than silently missing.
- **An Appendix or "State Specific Information" section** citing a state
  statute that overrides part of the generic criteria for that state only —
  most commonly a statutory minimum/maximum reauthorization or duration period
  that differs from the generic policy's duration (e.g., a state law requiring
  a minimum 12-month reauthorization once a patient has been stable on therapy
  for 2+ years, when the generic policy states 6 months), or a state law
  mandating coverage of a diagnosis/indication the generic diagnosis list does
  not otherwise include. When you find one: write it as its own separate,
  explicitly state-scoped segment — never let it silently change the default
  duration/diagnosis list for every other state.
- Any state-specific effective date, definition, or age restriction that
  differs from the general policy.

The default segment states the rule that applies absent a state override.
Each state override gets its own clearly labeled segment layered on top of —
never blended into — that default. If a state redirect and a state statutory
override both exist for different states in the same document, capture both
as separate segments; do not resolve them into a single averaged rule.

**While reading, also flag every instance of:**
- A condition that depends on another code's status — "if [other study] was
  inconclusive/unsuccessful," "not indicated once [other code] already qualifies
  using banked/prior material," "covered as an add-on to [base procedure]." These
  become **Code Dependencies** (below) — do not fold them into ordinary prose
  where the cross-code reference gets lost.
- A hard exclusion or contraindication stated before, or separately from, the
  positive indications list (pregnancy, incompatible implant, excluded anatomy
  target). These become a **Contraindication Gate** (below).
- Any implant, device, or imaging-environment safety-labeling condition. This
  becomes a **Device Safety Gate** (below).
- Any statement about whether prior testing or workup is, or is explicitly is
  NOT, required first. Check every section individually — the same policy can
  require prior workup in one region/indication and explicitly waive it in
  another.


## Step 2 — Classify

Use `references/classification-rules.md` to decide each variant's authorization
phase and dependency type. If the policy distinguishes Initiation vs Continuation
(or Initial/Renewal, Trial/Ongoing), write each as a **separate variant** — never
combined.

**Imaging-specific: region and modality branches count the same way.** If a
single code's coverage depends on which anatomic region is being imaged (MRA of
head/neck vs. MRA of peripheral arteries vs. MRA of chest — same CPT family,
different qualifying logic per region) or which modality was chosen (MRI vs. MRA
vs. contrast angiography as alternatives for the same clinical question), write
**each region or modality as its own named variant** — never merge them into one
AND-chain. A reviewer (and the downstream model) needs to evaluate "did this
patient qualify under the head/neck pathway" independently of "did this patient
qualify under the chest pathway," because the underlying conditions are
genuinely different, not sub-steps of the same test.

**State-specific segments follow the same never-merge rule.** A default
national/payer-baseline variant and any state-statute override identified in
Step 1 are different variants, not different phrasings of the same rule —
classify and write them separately, the same way you would two different
regions or two different phases.

## Step 3 — Draft the left side

For each variant, write declarative clinical criteria:

- State facts, not instructions ("Patient has a BMI > 35", never "Check if...").
- Make AND / OR logic explicit and use short numbered/lettered sub-items.
- Use the **exact verbatim language** from the policy — do not paraphrase.
- Always use "patient" (never "member"/"beneficiary").
- Include prescription criteria with all required fields when an Rx is required.
- Under each criterion, include a verbatim policy quote with page/section reference,
  and put the same verbatim excerpts in that criterion's `source_snippets`.
- Exclude billing modifiers, facility/technologist certification requirements,
  and any if-then/exclusionary reasoning from the left side.

Follow `references/quality-rules.md` for the full rules and
`references/examples.md` for the exact target structure.

### Exclusions — do NOT emit non-qualification content

A qualification criterion tests a fact about the **patient's clinical chart**.
If a requirement is checkable only from supplier/claim paperwork rather than the
patient's clinical record, it is claims-adjudication logic — reviewers delete
it. Never emit criteria in these categories, even when the policy states them
verbatim:

- **Order/requisition paperwork mechanics** — referring-order timing rules,
  required order elements (NPI, signature, dating rules), state forms.
- **Prior authorization / approval / billing** — prior-auth process, approval
  or authorization periods, reimbursement, claim submission, fee-schedule or
  CPT/HCPCS coverage statements, modifier rules.
- **Enrollment / eligibility** — "patient is enrolled in [state] Medicaid on
  the date of service" and similar program-eligibility rules.
- **Code bundling** — mutual-exclusion or same-day/month/period combination
  rules ("must not include X in the same month", "not both", NCCI-style edits).
  This is distinct from a genuine **Code Dependency** (below) — bundling rules
  are billing-side edits about what can be claimed together; a Code Dependency
  is a clinical condition where this code's medical necessity is contingent on
  another code's documented outcome. Keep the latter; drop the former.
- **Place-of-service / residency** — inpatient-vs-outpatient setting rules,
  unless the policy makes the setting a clinical coverage condition for the
  requested code.
- **Facility and equipment certification** — facility accreditation (e.g. ACR
  accreditation), unit FDA premarket-approval status, or technologist
  certification requirements. These gate whether a facility CAN bill the code
  at all, not whether THIS PATIENT qualifies for it. Exception: keep a
  requirement if the policy ties it to a patient-specific safety decision (e.g.
  a specific supervision/monitoring requirement tied to an implanted device
  during the scan — see Device Safety Gate below).
- **Radiologist workflow / turnaround** — report turnaround time, read
  assignment, or interpretation-billing rules, unless tied to an actual clinical
  decision point the policy makes a condition of coverage.
- **Generic documentation boilerplate** — "medical records support medical
  necessity", "service is medically necessary and does not duplicate another
  service", "an individualized plan of care exists", record-retention
  requirements. Include a documentation requirement ONLY when it tests a
  specific clinical fact (e.g. a signed order documenting a specific symptom,
  measurement, prior-test outcome, or trial-and-failure).

Anti-undercut guard (read carefully — over-cutting is as bad as over-generating):

- These exclusions apply only to criteria whose SOLE content is administrative.
  Never drop, weaken, or merge a genuine patient-clinical requirement —
  diagnosis, symptom or clinical finding, functional limitation, objective
  measurement or threshold, trial-and-failure, severity, home-use requirement,
  quantity limit, or frequency. When unsure whether content is a clinical
  qualification requirement, KEEP it.
- NEVER emit an empty criteria list. Every code the payer covers has at least
  one clinical medical-necessity requirement (diagnosis / symptom / clinical
  finding supporting the need). If everything you drafted matches an exclusion,
  you cut too much — go back to the policy and write the clinical requirements.
- When the policy allows exceeding a quantity limit with supporting
  documentation, write ONE conditional criterion ("Only evaluate if the ordered
  quantity exceeds [N] per [period]; if it does not, this criterion is met; if
  it does, the medical record must document [policy-specific justification]").
  Never convert a documentable exception into a hard cap.

### Code Dependencies — declare cross-code hinges explicitly

Some imaging codes are only medically necessary because of another code's
documented status. There are **two distinct patterns** — classify each
occurrence correctly, because they're written differently:

**1. Sequential/outcome dependency.** The code has its own independent
qualifying criteria, but ONE of those criteria is conditioned on another code's
outcome — usually that the other study was already attempted and failed, was
inconclusive, or is being deliberately avoided by using this study instead.
Write the dependency as its own numbered sub-item, in plain declarative form,
naming the other code and the required status:

```
- Add-On MRA for Runoff Vessel Identification: Patient meets both of the following:
1. A prior contrast angiography (CPT 75710) was performed and was unable to
   identify a viable runoff vessel for bypass
2. Exploratory surgery is not considered a reasonable course of action for this
   patient
```

Add a parallel `code_dependencies` note alongside the criterion when emitting
(see Step 4) — do not let the cross-code reference live only inside prose where
it could get lost during extraction-field generation. State explicitly:
- The other CPT/HCPCS code
- Whether this criterion requires that code to be **QUALIFIED** (already met its
  own criteria) or **DISQUALIFIED/RULED OUT** (failed, inconclusive, or its
  criteria were not met)
- The one-line clinical reason (why the dependency exists)

**2. Structural/bundling dependency (add-on codes).** The code is never billed
independently — it only exists in conjunction with a base procedure code, and
its own coverage is entirely derivative of that base code's qualification (e.g.,
a 3D-rendering add-on, a contrast-administration add-on). See
`references/classification-rules.md` Step 4 for how to classify these. Write the
dependency as the entire criterion, not a sub-item:

```
- Base Procedure Dependency: This code is covered only when CPT [base code]
  ([base code description]) is independently qualified for this patient. This
  code has no independent clinical indication of its own.
```

Never leave a cross-code hinge implicit. If you found dependency language while
reading the policy (per Step 1) but can't tell which pattern applies, default to
writing it as a sequential/outcome dependency (pattern 1) — a reviewer can
always simplify it later, but an omitted dependency silently produces wrong
qualifications.

### Contraindication Gate — evaluate before positive indications

Any condition the policy states as an absolute bar to coverage — regardless of
which indication otherwise applies — is a **Contraindication Gate**, not an
ordinary AND-condition buried inside one indication's criteria. Write it as its
own named criterion, and make clear in the declarative text that it applies
across the whole code (or whole order type), not just the pathway you happened
to be drafting when you found it:

```
- Contraindication — Viable Pregnancy: Patient is not currently pregnant with a
  viable pregnancy, if this study uses ionizing radiation OR the policy
  otherwise excludes imaging during pregnancy.
```

If the policy states multiple absolute contraindications (pregnancy,
incompatible implant, claustrophobia history, targets excluded anatomy), write
each as its own numbered Contraindication Gate criterion rather than merging
them into one block — this keeps each one independently testable and prevents
one contraindication's evidence from masking another's absence.

### Device Safety Gate — implant/equipment interaction pathways

When a policy conditions coverage on an implanted device's compatibility with
the imaging environment (most commonly MRI-conditional pacemakers, ICDs, or
CRT devices), write the full branch — do not compress the safety checklist into
a single sentence:

```
- Device Safety — FDA-Labeled Pathway: Patient's implanted device
  (pacemaker/ICD/CRT-P/CRT-D) is labeled by the FDA for use in this MRI
  environment, and the scan is performed according to that labeling.

- Device Safety — Non-Labeled Pathway (all required if the device is not
  FDA-labeled for this MRI environment):
1. Field strength and operating mode match the policy's specified parameters
2. Device system has no fractured, epicardial, or abandoned leads
3. [each remaining facility-checklist item as its own numbered sub-item —
   do not bundle multiple checklist requirements into one sub-item]
```

Number every discrete checklist requirement separately, even if the source
policy writes them as one flowing paragraph — a bundled checklist produces one
extraction field for the whole thing instead of one per requirement (same
failure mode as any other over-long block, see Structure Rules).

### Dual-Test Rule — only one of two studies covered absent both being necessary

When a policy states that two modalities (e.g., MRA and contrast angiography)
aren't both indicated for the same diagnostic purpose unless medical necessity
for both is separately demonstrated, write it as its own criterion, and treat
it as a Code Dependency (pattern 1 above) against the other modality's code:

```
- Dual-Test Limitation: This study and [other modality] (CPT [code]) are not
  both indicated for the same diagnostic purpose prior to anticipated therapy,
  unless the ordering practitioner documents the medical need to perform both.
```

### Prior-Test Requirement — check every region/indication individually

Do not assume a policy is internally consistent about whether prior
testing/workup is required first. The same policy can require it in one
region's criteria and explicitly waive it in another (e.g., one NCD required
prior CA to have failed before covering an MRA add-on, but explicitly said a
different indication needed no prior imaging at all). For each variant you
draft, check the policy text for that specific variant and write what it
actually says — do not carry a prior-test requirement over from a different
region/indication in the same policy, and do not assume one is required just
because it's common in similar policies.

### Base condition criterion — always present

Every covered code has a clinical reason to exist. Always include a criterion
that the patient has the condition or clinical question the study addresses,
when the policy states OR implies it (including via the policy's definition of
the study's purpose — e.g. an NCD describing MRA of the head/neck as used to
evaluate specific vessels for anticipated surgery implies "patient has a
condition of the head/neck for which surgery is anticipated and may be
appropriate based on the study's findings"; a policy covering MRI for disc
disease implies "patient has signs/symptoms of suspected disc disease"). A
draft whose only content is device/field-strength specs and safety gates, with
no patient-condition or clinical-indication requirement, is incomplete.

### General-provisions sweep — testable clauses only

Policies (especially state Medicaid handbooks) bury real qualification clauses
in their general coverage sections. After drafting from the code-specific
section, re-scan the general provisions and include the clauses the policy
states as coverage conditions that a reviewer can actually test for this
patient and item:

1. **Convenience / preference exclusions** — "not furnished primarily for the
   convenience of the patient, caregiver, or provider", "not for food
   preference". Write as a declarative criterion. These clauses hide anywhere —
   definitions sections, "conditions of coverage" lists, regulation citations
   (e.g. a state reg like "Section 6(1)(d)") — so grep the WHOLE document for
   "convenience" and "preference" before you finish drafting; missing one is a
   recall failure.
2. **Age-conditional medical-necessity standards** — e.g. Florida Medicaid's
   ≥21 severity standard vs the EPSDT rule for under-21. Capture the age split
   explicitly rather than emitting the adult standard unconditionally.
3. **Facility/setting requirements tied to a clinical safety condition** —
   e.g. a requirement that a specific level of monitoring, supervision, or
   life-support capability be present during the scan (most common in Device
   Safety Gate contexts). Do not include ordinary site-of-service billing rules
   (outpatient vs. inpatient) that aren't tied to a patient-specific safety
   decision — those stay excluded per the Exclusions section above.
4. **Not experimental / investigational** and **treatment-plan** clauses —
   include when the policy states them as coverage conditions for the item's
   category (common in state-Medicaid medical-necessity sections).

Still excluded from the sweep: definitions-section language emitted standalone,
EPSDT generalities with no testable condition, "individualized / not in excess
of the patient's needs" coverage-standard boilerplate with no specific fact to
verify, and noncovered-product lists for products other than the requested
code. Never emit a citation line or "Found in: ..." notation as its own
criterion — citations belong inside the criterion they support.

In particular, do NOT transcribe a state Medicaid "definitions of medical
necessity" block (e.g. Florida's 59G-1.010 list: "individualized, specific,
consistent with symptoms", "not experimental or investigational" as a bare
definition, "furnished in a manner not primarily intended for the convenience
of the provider" restated as generic MN prose, "reflect the level of service
that can be safely furnished") as a run of separate criteria. From that block,
keep exactly two things when applicable: the age-conditional severity/EPSDT
split (sweep item 2) and a single convenience-exclusion criterion (sweep
item 1). The rest is coverage-standard boilerplate — reviewers strip it.

### Frequency/interval limits and thresholds — copy the SEMANTICS exactly

Imaging policies are less likely than DME to state a flat per-month unit cap,
but they frequently state **repeat-study interval limits** ("no more than one
[study] per [N days/months] absent new symptoms or a change in clinical
presentation") and region-specific thresholds (vessel counts, size cutoffs).
Numbers are usually right; the failure mode is modulating the rule around the
number. Copy limit semantics exactly as the policy states them, in both
directions:

- **Hard cap in policy → hard cap in criteria.** NEVER add an escape hatch the
  policy does not grant ("OR the medical record documents medical necessity for
  an earlier repeat study..."). If the policy states an interval with no
  exception, the criterion is the interval alone.
- **Overridable interval in policy → conditional in criteria.** If the policy
  allows an earlier repeat study with documentation (new symptoms, changed
  presentation, treatment change), preserve that path in conditional form. Do
  NOT harden it into an absolute interval.
- **Ranges keep both bounds.** "Aneurysm greater than 4cm and not exceeding
  6.5cm" must keep the upper bound — dropping either bound changes the rule.
- **Vessel/region/device-compatibility lists are closed.** When the policy
  enumerates which vessels an MRA covers (carotid, circle of Willis, vertebral
  or basilar arteries, venous sinuses), which devices an implant-safety pathway
  applies to, or which regions a code's criteria apply to, copy the list
  exactly; never add an item the policy does not name.
- **Disjunctions stay disjunctions.** When the policy accepts alternatives —
  "tumor, aneurysm, vascular malformation, OR vascular occlusion/thrombosis",
  "MRA OR contrast angiography" — keep EVERY alternative in the criterion.
  Never narrow an "or" to the single branch that seems primary: dropping a
  branch rejects patients the policy covers.
- Never emit the same criterion twice (exact or near-duplicate).

### Code differentiation — with/without contrast, unilateral/bilateral, region scope

When the policy or CPT code description attaches coverage attributes that
differentiate the requested code from its neighbors, capture them as criteria:
covered-age restrictions, region scope (e.g. brain vs. brain plus orbit/face/
neck), and the specific attribute that distinguishes this code from a sibling
code (e.g. "without contrast" vs. "with and without contrast" — documentation
of whether contrast was administered and why; unilateral vs. bilateral — which
side(s) are being imaged and the clinical basis for each). If the policy
distinguishes the requested code from a sibling code by a requirement, that
requirement is a criterion.

## Step 4 — Self-check, then submit

Before submitting, verify: payer scope correct — every criterion is attributed
to the right payer/plan category, and (for Medicare only) the right NCD vs.
jurisdiction-specific LCD; order/requisition fields complete; Initiation/
Continuation split AND region/modality split AND state-override split (every
named region, modality, or state variant is its own segment, never merged);
every criterion has a verbatim quote; no paraphrase; no reasoning on the left
side.

**Payer/jurisdiction checks:**
- If the payer is traditional Medicare and any criterion is sourced from an
  LCD, is the specific MAC jurisdiction named (not just "an LCD")?
- If the policy spans multiple payers or states, is each criterion clearly
  scoped to the payer/state it actually applies to, rather than written as if
  it applied universally?
- Did Step 1's scan surface any state redirect table or state statute
  override? If so, is each one written as its own segment rather than folded
  into the default criteria, and is any state redirected to a separate policy
  document excluded from this order type entirely (not silently given the
  default criteria)?

**Imaging-specific checks:**
- Every Code Dependency you found while reading the policy is written out
  explicitly, naming the other CPT/HCPCS code and whether it must be QUALIFIED
  or DISQUALIFIED/RULED OUT — none left implicit in prose.
- Every Contraindication Gate is written as its own criterion, not folded into
  one indication's AND-chain.
- Any Device Safety Gate has every checklist item as its own numbered sub-item —
  none bundled into a single sentence.
- Any Dual-Test Rule is present if the policy has ANY "only one of two studies"
  language, and is written as a Code Dependency against the other modality.
- Every variant states whether prior testing is required, not required, or not
  addressed — checked against that specific variant's own policy text, not
  assumed from another variant in the same policy.

Then run a **numeric fidelity pass**: for every number, threshold, interval
limit, age, time window, and vessel/region/device list in your draft, re-read
the exact policy sentence it came from (your source snippet) and confirm (a) the
value matches, (b) both bounds of any range are present, (c) the exception
semantics match — no added escape hatch, no dropped override, and (d) enumerated
vessel/device/code lists match exactly. Fix any drift before emitting.

Then call the **`emit_criteria`** tool exactly once with the structured result.
Map each criterion to the requested primary code(s) it applies to. The
`emit_criteria` call is the ONLY way your output is captured — a chat message is
not enough.

If a reviewer returns issues, revise the criteria and call `emit_criteria` again
with the corrected set.
