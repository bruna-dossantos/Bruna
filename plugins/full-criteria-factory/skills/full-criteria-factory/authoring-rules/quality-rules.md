# Criteria Quality Rules

These rules come directly from Tennr's internal SOPs, Stacey's review process, and Bruna's feedback on real criteria iterations. Apply all of them before declaring criteria complete.

---

## The Mental Model

Think of criteria as having two distinct jobs:

- **Left side (The Judge)**: Sets the rules. Written for a human reviewer. Says exactly what insurance requires. No interpretation, no reasoning — just the requirements.
- **Right side (The Detective)**: Finds the evidence. Written for the AI model. Tells it where to look and what to look for in the actual documents. No decisions — just extraction.

Stacey's team uses this memory aid: "The left side is the judge — the decision maker. The right side is the detective — searching for evidence."

---

## Terminology Rules

- **Always use "patient"** — never "member" or "beneficiary" anywhere in output, criteria text, notes, or labels. These terms come from payer policy language but Tennr's system uses "patient" universally. Replace every instance regardless of what the source policy says.

---

## Note Style Rules

- **Inline sentence only (Option A)** — when adding a clarifying note to a criterion, write it as a plain inline sentence immediately after the requirement. Never use a parenthetical format.
  - ✅ Correct: `"The start date of therapy is the date of service/device delivery date."`
  - ❌ Wrong: `"(Note: the start date of therapy is the date of service/device delivery date.)"`
- The parenthetical style causes reviewer flip-flopping and inconsistency across criteria. Option A is the only permitted format.

---

## Left Side Rules

### Do:

- Write in declarative, factual statements: "Patient has a BMI > 35" ✅
- Use **AND** and **OR** explicitly — don't leave logic implicit
- Break complex logic into short numbered sub-items
- **Use the declarative numbered template — never a run-on sentence.**
  - Requirement (OR): `The patient's medical records must document at least one of the following (1 or 2 or 3):` then `1. …` `2. …` `3. …` — one alternative per numbered line.
  - Requirement (AND): `The patient's medical records must document all of the following:` then numbered items.
  - Exclusion / Contraindication Gate: `The patient does NOT have any of the following: 1. … 2. …` — a negative gate evaluates TRUE when none are present, so it needs no extra pass-through.
  - ✅ `The patient's medical records must document at least one of the following (1 or 2 or 3): 1. Signs or symptoms of disease 2. Suspicion of disease 3. A preliminary or provisional diagnosis`
  - ❌ `The study is medically appropriate given the patient's symptoms and preliminary diagnosis, and the record documents the signs and symptoms that warrant the test.` (run-on; alternatives buried)
- **Give a conditional criterion an explicit pass-through.** A criterion that only applies in certain cases must end with a plain scoping sentence, so the strict, missing→FALSE evaluator doesn't sink the code when the trigger is absent: `This requirement applies only when …; otherwise this criterion is considered met.` (Not needed for negative gates, which already pass when absent.)
- Use the exact verbatim language from the policy source — do not paraphrase or simplify
- Bold key terms and conditions
- Italicize document-type indicators (_Found in: Prescription_, _Found in: Medical Records_)
- Specify signature and date requirements when the policy demands them
- Include the specific provider type when relevant (physician vs. NP/PA vs. RT)
- Number each distinct requirement so the right side can reference them
- Include a verbatim policy quote with page/section reference under each criterion block

- **Declare every cross-code hinge explicitly (Code Dependency).** If a
  criterion's medical necessity depends on another CPT/HCPCS code's
  qualification or disqualification outcome — e.g. "MRA is covered to identify
  a runoff vessel when a prior contrast angiography (CPT 75710) was unable to
  do so" — name the other code and the required status (QUALIFIED or
  DISQUALIFIED/RULED OUT) in the criterion text itself. Never let a cross-code
  reference live only in the surrounding narrative where it can be dropped.
- **Write absolute exclusions as their own Contraindication Gate criterion.**
  Conditions that bar coverage regardless of which indication otherwise applies
  (pregnancy, incompatible implant, excluded anatomy target) get their own
  named criterion, evaluated ahead of the positive indications — don't bury
  them inside one indication's AND-chain where they'd only apply to that one
  pathway.
- **Write region and modality branches as separate segments**, the same way
  Initiation/Continuation phases are separated. A code whose criteria differ by
  anatomic region (e.g. MRA of head/neck vs. MRA of chest) or by modality choice
  (MRI vs. MRA vs. contrast angiography) needs one named segment per
  region/modality, never one merged block.

### Don't:

- ❌ Include reasoning or "if-then" decision logic on the left side
- ❌ Write extraction instructions on the left side ("Check if...", "Look for...")
- ❌ Bundle too many requirements into one long block (breaks extraction generation)
- ❌ Use vague language ("appropriate documentation", "sufficient evidence")
- ❌ Reference competitor products or brand names that don't apply to this customer
- ❌ Include criteria that Medicare doesn't actually require (e.g., edema for lymphedema)
- ❌ Mix Medicare and non-Medicare logic in the same criteria block
- ❌ Use "member" or "beneficiary" — always use "patient"
- ❌ Leave a Code Dependency implicit in prose ("this is typically done after the
  other study fails") instead of naming the specific code and required status
- ❌ Merge a Contraindication Gate into one indication's criteria instead of
  writing it as its own always-evaluated-first block
- ❌ Merge two regions' or two modalities' criteria into one AND-chain

### Referring order fields — always include all of these when an order/requisition is required:

1. Study/item name or CPT/HCPCS code (with synonyms)
2. Ordering practitioner's signature
3. Patient name
4. Ordering practitioner's name or NPI
5. Date (with logic: signature date > recertification date > most recent date)
6. Any additional fields the policy requires (e.g., clinical indication for the
   study, contrast requested, laterality/region)

---

## Right Side Rules

### Do:

- Write one extraction field per discrete criterion (not one giant field per section)
- Name the document type explicitly: "Find in the prescription document...", "Find in the sleep study..."
- Include alternate terminology and synonyms (e.g., "CPAP", "Auto-PAP", "E0601", "continuous positive airway pressure")
- Be specific about what text or value to look for
- Keep each extraction prompt short and targeted
- Split long criteria into multiple extraction fields rather than cramming them into one

### Don't:

- ❌ Include reasoning: "Determine whether the patient qualifies based on..." ❌
- ❌ Include scoring logic: "Calculate the AHI and determine if it meets the threshold" ❌
- ❌ **Include conditional/if-then logic: "If the BMI is above 35, then..." — this is always a defect, never a style choice. Flag as HIGH severity.**
- ❌ **Include exclusionary language: "Do NOT accept X", "Only X qualifies, not Y", "Reject if..." — this is always a defect, same severity as conditional logic. The right side extracts evidence only; it never decides what qualifies or disqualifies.**
- ❌ Make the extraction prompt longer than the criterion itself
- ❌ Write a single extraction field that covers an entire complex criteria block — it will truncate

### Reasoning vs. extraction — examples:

| ❌ BAD (reasoning in extraction)                                                                           | ✅ GOOD (pure extraction)                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| "Determine if the patient was using prescribed oxygen settings or room air"                                | "Find documentation of oxygen settings used during the blood gas test. Look for 'prescribed oxygen', 'room air', or specific liter flow settings."                       |
| "Check if the AHI is less than 5 and evaluate whether it disqualifies the patient"                         | "Find the AHI (Apnea-Hypopnea Index) value recorded in the sleep study."                                                                                                 |
| "Assess whether the face-to-face visit was prior to the sleep study"                                       | "Find the date of the face-to-face encounter. Note: a face-to-face can be documented as Telehealth, Televisit, 'show up', 'present', or 'seen'."                         |
| "If the hypopnea scoring standard used is AASM Rule 1A, reject — only AASM 1B (4% desaturation) qualifies" | "Find the hypopnea scoring standard documented in the sleep study. Look for 'AASM Rule 1A', 'AASM 1B', '3% desaturation', '4% desaturation', or equivalent terminology." |

---

## Structure Rules

### Criteria block length:

- **Short blocks generate better extractions.** When a criteria block is very long, the model only generates 1 extraction field for the whole thing instead of one per item.
- If a single criteria section has more than ~5 sub-items, split it into two labeled sections.
- Example: Instead of one giant "Criteria 2: Sleep Study (PSG or Home Study)" block with 4 nested sub-requirements, break it into "Criteria 2A: Sleep Study Performed" and "Criteria 2B: Sleep Study Results."

### AND/OR logic:

- Use explicit **AND** / **OR** labels (highlighted or bolded) between criterion blocks
- Don't leave logic to be inferred from sentence structure
- For alternative pathways (patient must meet Criteria 1 OR Criteria 2), label them clearly: "The patient must meet EITHER criteria 1 OR 2 below:"

### Document types to know:

- **Referring Order / Requisition**: The order for the imaging study. Must be
  signed and dated. Contains study name/code, patient name, ordering
  practitioner info, and the clinical indication for the study.
- **Medical Record / Clinical Note**: Encounter documentation from the ordering
  or treating practitioner — signs/symptoms, exam findings, and treatment
  history supporting the indication. Must be signed and dated.
- **Prior Imaging or Procedure Report**: The report from an earlier study this
  code's criteria reference (e.g., the contrast angiography a code's Code
  Dependency requires to have already been attempted). Contains study type,
  date, and result/impression.
- **Device Card / Device Interrogation Report**: For implant-safety pathways —
  device type, FDA MRI-labeling status, lead configuration, and
  interrogation/reprogramming date and settings.
- **Contrast Allergy / Contraindication Documentation**: Documented allergy or
  contraindication to a specific contrast agent (iodinated or gadolinium-based).
- **Laboratory Results**: Renal function (creatinine/eGFR) when contrast is
  involved, pregnancy status when relevant, or other lab values the policy ties
  to the study's safety or indication.
- **Progress Notes / LMN**: Letter of Medical Necessity or clinical progress
  notes from the treating practitioner, when the policy requires one beyond the
  referring order and medical record.

---

## Payer-Specific Rules

**This skill must produce correct criteria for whatever payer(s) the source
policy actually governs — Medicare, Medicaid, Medicare Advantage, or
Commercial/Marketplace. Do not default to Medicare-specific logic (NCD-before-LCD,
MAC jurisdiction) unless the payer in question is actually traditional
Medicare.** Every payer type has its own equivalent "which jurisdiction does
this criterion actually apply to" question — identify and answer it before
drafting, regardless of payer.

### Medicare (traditional/FFS):

- **Check for a governing NCD first.** Imaging — especially MRI and MRA — is far
  more likely than DME to have a National Coverage Determination that binds
  nationally and pre-empts local MAC discretion. Only fall back to an LCD
  (Noridian, CGS, or another MAC) for indications the NCD leaves to local
  discretion, or for modalities with no controlling NCD (e.g., most CT and
  ultrasound criteria are LCD-governed).
- **When falling to an LCD, name the specific MAC jurisdiction it was issued
  under** (e.g., Noridian JD DME, CGS JD, Palmetto GBA) — never cite "an LCD"
  generically. This is the Medicare-specific version of the jurisdiction
  precision every payer type requires (see below).
- When both an NCD and a supplementing LCD apply, cite each criterion to the
  correct source — do not present LCD-only language as nationally binding, and
  do not present NCD language as something a local MAC could narrow.
- Medicare is the strictest baseline — MA and Medicaid may be looser.
- Do NOT include state-specific Medicaid requirements in a Medicare order type.

### Medicare Advantage (MA):

- MA plans must follow Medicare rules at minimum, but individual plans may add requirements.
- When writing MA criteria, note: "Follows Medicare baseline unless plan-specific policy overrides."
- Jurisdiction precision for MA: identify the specific MA plan/product — MA
  plans are not interchangeable with each other or with traditional Medicare.

### Medicaid:

- State-specific. Criteria vary significantly by state. If writing Medicaid criteria, confirm which state.
- Don't conflate Medicaid with Medicare Advantage or Medicare — these are distinct.
- Jurisdiction precision for Medicaid: identify the specific STATE Medicaid
  program each criterion applies to. Many MCOs publish one umbrella policy
  document that governs several state Medicaid programs at once with
  per-state statutory carve-outs layered in — see State-Specific Callouts below.
  Never apply one state's override to a different state's patient.

### Commercial / Marketplace:

- Typically most permissive. Often prescription-only for many DME codes.
- Confirm whether the customer has a specific payer contract requirement.
- Jurisdiction precision for Commercial: identify the specific payer AND
  plan/product — a Marketplace product from a given payer can carry different
  rules than that same payer's standard commercial plan, even within one
  policy document.

---

## State-Specific Callouts

Regardless of payer type, scan every policy document for state-specific
carve-outs, redirects, or statutory overrides — these appear constantly in
multi-state MCO and national-commercial documents and must never be merged
into one generic order type.

**What to look for:**
- **A scope/redirect table** at the top of the policy sending specific states
  to a wholly separate policy document (e.g., "for Ohio, refer to
  [Ohio-specific policy]"; "for Arizona, refer to the state's Medicaid clinical
  policy"). When present: do NOT write criteria for that state under this
  order type — the policy explicitly does not govern it. Flag the redirect
  rather than silently omitting it or silently applying the default criteria.
- **An Appendix or "State Specific Information" section** citing a state
  statute that overrides part of the generic criteria for that state only.
  The most common pattern is a statutory minimum/maximum reauthorization or
  duration period that differs from the generic policy (e.g., a state law
  requiring reauthorization no more frequently than every 12 months once a
  patient has 2+ years of sustained response, when the generic policy default
  is 6 months), or a state law mandating coverage of a diagnosis/indication
  the generic diagnosis list doesn't otherwise name. When present: write it as
  its own separate, explicitly state-scoped segment layered on top of the
  default — never blend it into the default so it silently changes the rule
  for every other state too.
- Any state-specific effective date, definition, or age restriction that
  differs from the general policy.

**Format:** the default segment states the rule that applies absent a state
override. Each state override is its own clearly labeled segment (e.g.,
"Illinois — Statutory Reauthorization Override," "Ohio — Excluded, See
Separate Policy"). If a document has multiple different state overrides,
capture each one separately — do not average them into a single compromise
rule.

---

## Common Failure Modes to Catch

1. **Reasoning bleeding into extractions** — Most common error. Stacey's team is specifically trained to spot this. Check every right-side field.
2. **Missing prescription fields** — Especially NPI, date logic, and item code synonyms.
3. **Vague extraction prompts** — "Find documentation of the diagnosis" is too vague. "Find ICD-10 code G47.33 or diagnosis of 'obstructive sleep apnea' or 'OSA'" is specific.
4. **Payer mismatch** — Criteria written for Medicare being applied to Medicaid or MA patients.
5. **Outdated LCD** — LCDs are periodically updated. Always check the "effective date" on the LCD.
6. **One extraction per complex block** — Should be one extraction per discrete criterion.
7. **Competitor product references** — Especially in custom criteria. Don't include product names from other vendors.
8. **Criteria the payer doesn't require** — Don't add requirements beyond what the policy actually states.
9. **Facility/technologist certification bleeding into criteria** — Do NOT include facility accreditation, unit FDA-premarket-approval status, or technologist certification requirements in patient-qualification criteria. These gate whether a facility can bill the code at all, not whether this patient qualifies. Leave them to the billing/credentialing workflow, unless the policy ties them to a patient-specific safety decision (Device Safety Gate).
10. **Initiation vs. Continuation (and any similar breakouts, including region/modality)** — If the policy distinguishes between Initiation and Continuation criteria, named phases (Initial vs. Renewal, Acute vs. Chronic, Trial vs. Ongoing), OR — imaging-specific — anatomic regions or modality choices (MRA of head/neck vs. MRA of chest; MRI vs. MRA vs. contrast angiography) — write each as a **separate criteria segment**, never combined into one block. Each segment gets its own named criteria entry so Tennr can evaluate them independently.
11. **Conditional logic on the right side** — Any if-then or conditional logic on the extraction side is always a HIGH severity defect. Never add it; always remove it.
12. **Exclusionary language on the right side** — Any "Do NOT accept", "Only X qualifies", or "Reject if" language on the extraction side is always a HIGH severity defect. Never add it; always remove it.
13. **Paraphrased policy language** — All criteria text must use exact verbatim wording from the source policy. Paraphrased or simplified versions introduce inaccuracies and must be corrected against the source document.
14. **Wrong terminology** — "Member" or "beneficiary" in any output. Always replace with "patient."
15. **Parenthetical notes** — Any note formatted as `(Note: ...)` must be converted to an inline sentence (Option A style).
16. **Implicit Code Dependency** — A criterion that clinically depends on another code's outcome ("covered when the other study failed," "not indicated once banked material already qualifies") but doesn't name the specific CPT/HCPCS code and the required status (QUALIFIED or DISQUALIFIED/RULED OUT). Every cross-code hinge must be explicit, not left to be inferred from surrounding prose.
17. **Contraindication Gate folded into one indication** — An absolute exclusion (pregnancy, incompatible implant, excluded anatomy) written inside a single indication's AND-chain instead of as its own criterion that applies across the whole code. This makes the exclusion invisible to any other pathway it should also block.
18. **Bundled device-safety checklist** — A Device Safety Gate (e.g., MRI-conditional pacemaker checklist) written as one flowing sentence instead of one numbered sub-item per discrete requirement. Produces one extraction field for the whole checklist instead of one per requirement.
19. **NCD/LCD conflation** — Citing an LCD as if it were nationally binding, or citing an NCD as though a local MAC could narrow it. Check and cite the correct source for each criterion.
20. **Medicare-specific logic applied to a non-Medicare payer** — Using NCD/LCD/MAC-jurisdiction sourcing patterns on a Medicaid, MA, or Commercial policy, or vice versa. Each payer type has its own jurisdiction question (state for Medicaid, plan for MA/Commercial, MAC for Medicare) — don't substitute one for another.
21. **State-specific override merged into the default criteria** — A state statute or redirect found in an appendix/scope table gets folded into the generic order type instead of written as its own state-scoped segment. This silently changes the rule for every other state (if blended in) or silently keeps serving a state the policy explicitly excludes (if a redirect is dropped). Always check Step 1's state-callout scan was actually performed and every finding was captured as its own segment.
