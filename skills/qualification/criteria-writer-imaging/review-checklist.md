# Criteria Review Checklist — Imaging

Detailed reference for all 12 checks run during a criteria review. Each check includes the rule, what to look for, and bad vs. good examples. Checks 11 and 12 are imaging-specific additions (Code Dependency validity and Contraindication/Device Safety Gate placement) — the other ten apply the same way they do to DME criteria.

---

## Check 1 — Policy Alignment

**Goal:** Confirm the criteria faithfully represent the source payer policy — nothing added, nothing missing.

**What to look for:**

- Header metadata (payer, plan, state, code) matches the policy document
- All Medically Necessary conditions from the policy appear in the criteria
- All Not Medically Necessary / exclusion conditions are captured
- Quantity limits and clinical timing rules (e.g. re-evaluation windows) are present when the policy specifies them
- Criteria list open-ended policy lists with "including, but not limited to" language where applicable
- No criteria appear that cannot be traced to the policy text
- General-provisions clauses that ARE qualification criteria are captured: convenience/preference exclusions ("not primarily for the convenience of the patient or caregiver") and age-conditional medical-necessity standards (e.g. adult severity standard vs EPSDT for under-21)
- **Imaging-specific:** every anatomic region or modality the source NCD/LCD names for this code is represented as its own segment — a policy naming four covered regions (e.g. head/neck, peripheral arteries, abdomen/pelvis, chest) but criteria covering only two is a miss, not a scope choice
- **Imaging-specific:** if both an NCD and a supplementing LCD apply, criteria drafted from the LCD aren't presented as nationally binding, and criteria drafted from the NCD aren't presented as something a local MAC could override
- **Any payer:** if the source document contains a state redirect table or a state-specific statutory override (appendix, "State Specific Information," etc.), is each one captured as its own segment rather than folded into — or silently dropped from — the default criteria?

Do NOT treat the absence of authorization periods, billing timing, or claim-submission rules as a miss — those are non-qualification content (see Check 10).

**Bad:**

> Policy says: "Oxygen may be covered for cluster headaches."
> Criteria omits cluster headaches entirely from the covered indications list.

**Good:**

> Pathway C includes: "Patient has a diagnosis of cluster headaches."

**Bad (over-broadens):**

> Policy says coverage requires PaO2 ≤ 55 mmHg.
> Criteria says: "Patient has low oxygen levels."

**Good:**

> "Patient meets one of the following qualifying laboratory values obtained while breathing room air:
> a. Arterial PaO2 equal to or less than 55 mmHg; OR
> b. Oxygen saturation (SaO2 or SpO2) equal to or less than 88%"

---

## Check 2 — Left-Hand Statement Review

**Goal:** Every left-side statement must be a plain-English declaration of what must be true — not an instruction, not a search command, and not reasoning.

**Rules:**

- Use declarative form: "Patient has X" / "Item is Y" / "Provider must be Z"
- Never use instructional form: "Check if...", "Determine whether...", "Look for...", "Evaluate..."
- No right-hand language: "Medical records document..." → belongs on the right; left says "Patient has been diagnosed with..."
- AND/OR must be explicit between all blocks — never implied by sentence structure
- Phrasing like "There is documentation of..." is acceptable (style preference only); only flag if it causes genuine ambiguity

**Bad (instruction form):**

> "Check if the patient has a diagnosis of COPD or chronic lung disease."

**Good (declarative):**

> "Patient has a diagnosis of at least one of the following chronic conditions:
> a. Chronic obstructive pulmonary disease; OR
> b. Chronic lung disease"

**Bad (right-hand language on left):**

> "Medical records document that the patient has a qualifying oxygen saturation level."

**Good:**

> "Patient's oxygen saturation (SaO2 or SpO2) is equal to or less than 88% while breathing room air."

**Bad (implied AND/OR):**

> "Patient has COPD. Patient has documented hypoxemia."

**Good:**

> "Patient has COPD; AND
> Patient has documented hypoxemia while breathing room air."

---

## Check 3 — Right-Hand Extraction Review

**Goal:** Every extraction field must tell the LM where to find evidence — not evaluate, decide, or score it.

**Rules:**

- Right side = pure extraction: "Find the value of X in document Y"
- No thresholds or qualifying decisions: numbers and cutoffs belong on the left
- No if-then logic: "If AHI > 15, flag as qualifying" is forbidden
- No scoring: "Calculate total events and compare to threshold" is forbidden
- Extractions must be specific enough to avoid false positives
- When false-positive risk is high, add explicit "do not extract" guidance

**Bad (decision logic in extraction):**

> "Find the AHI value and determine whether it meets the threshold for CPAP qualification."

**Good:**

> "Find the AHI (Apnea-Hypopnea Index) value recorded in the sleep study report."

**Bad (threshold on right side):**

> "Extract the oxygen saturation level. If it is equal to or less than 88%, the patient qualifies."

**Good:**

> "Find any oxygen saturation value (SaO2 or SpO2) recorded while breathing room air. Look for 'room air saturation,' 'SpO2 on room air,' or 'baseline O2 sat.'"

**Bad (false-positive risk unaddressed):**

> "Find documentation of desaturation during sleep."

**Good:**

> "Find oxygen saturation values recorded during a sleep study, polysomnography, or nocturnal oximetry report. Do not extract daytime pulse oximetry values or values recorded while on supplemental oxygen."

---

## Check 4 — Left/Right Match

**Goal:** Every left-side criterion has exactly one or more corresponding extraction fields, and every extraction field maps back to a left-side criterion.

**What to flag:**

| Issue                   | Description                                                                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Orphaned left criterion | A left-side requirement exists with no extraction field — the LM has no way to find evidence for it                                      |
| Orphaned extraction     | An extraction field looks for something not required by the left side                                                                    |
| Mismatched scope        | Extraction retrieves evidence for the wrong criterion (e.g., extraction for Pathway B fires when Pathway A criterion is being evaluated) |
| Over-broad extraction   | A single extraction field covers an entire multi-item criteria block — should be split                                                   |

**Bad (orphaned left criterion):**

> Left: "Patient must have a qualifying face-to-face encounter within 30 days prior to the order date."
> Right: No extraction field for the face-to-face date or timing.

**Good:**

> Left criterion exists. Right has: "Extract the date of the face-to-face encounter. Compare to order date — encounter must be within 30 days prior."

**Bad (over-broad extraction):**

> One extraction field: "Find all documentation of the patient's oxygen qualifications."

**Good:**

> Separate fields for: PaO2 value, SpO2 value, condition diagnosis, hypoxemia symptoms.

---

## Check 5 — LM Findability

**Goal:** Every criterion must be locatable in real patient documents. Abstract, inferred, or policy-only requirements cannot be found.

**What to flag:**

- Criteria using policy concepts that don't appear in documents (e.g., "medically necessary" — this is a conclusion, not a findable fact)
- Criteria requiring the LM to infer a conclusion from indirect evidence
- Specified document types that don't actually contain the required information (e.g., looking for a diagnosis in the prescription when it's only in the clinical notes)
- Criteria that require comparing dates across documents without guidance on what to do when dates conflict

**Bad (abstract/unfindable):**

> "Patient's condition is appropriate for home oxygen therapy."

**Good:**

> "Patient has a documented diagnosis of at least one of the following: [list of ICD-10-codeable conditions]"

**Bad (wrong document type):**

> "Find the qualifying PaO2 value in the Physician Written Order."

**Good:**

> "Find the qualifying PaO2 value in the ABG report or laboratory results." (Tags: Medical Record)

---

## Check 6 — Grammar & Formatting

**Goal:** Consistent, clean formatting throughout the criteria block.

**What to check:**

- Spelling and grammar — no typos
- AND / OR — always ALL-CAPS; flag any "and" or "or" used as logical operators in lowercase
- Numbering — no skipped numbers; consistent style within a block (don't mix A/B/C and 1/2/3 in the same list)
- Document type names — capitalized consistently everywhere they appear
- Medical terms — consistent capitalization (e.g., always "Oxygen saturation" or always "oxygen saturation" — not both)
- Spacing — no double spaces, missing spaces after colons, or inconsistent line breaks

**Bad:**

> "Patient has an AHI of at least 15 events per hour and total apneas + hypopneas ≥ 30"

**Good:**

> "Patient has an AHI of at least 15 events per hour AND total apneas + hypopneas ≥ 30"

**Bad (mixed numbering):**

> "A. Condition 1
> B. Condition 2 3. Condition 3"

**Good:**

> "A. Condition 1
> B. Condition 2
> C. Condition 3"

---

## Check 7 — Structure Issues

**Goal:** Well-structured criteria blocks that the extraction model can parse cleanly.

**What to flag:**

| Issue                          | Rule                                                                                |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| Block too long                 | More than ~5 sub-items in a single criteria block → split into two named sub-blocks |
| Merged initiation/continuation | These must always be separate named segments                                        |
| Missing Tags                   | Every extraction field must end with `(Tags: [Document Type Name])`                 |
| Mismatched Tags                | Tag name doesn't match a document type defined in Doc Criteria                      |
| Extraction not indented        | Extraction fields must be indented under their parent left-side criteria            |

**Bad (too long):**

> One block with 9 sub-items covering qualifying conditions, lab values, symptom documentation, timing rules, and provider type.

**Good:**

> Split into "Qualifying Diagnosis", "Lab Values", and "Symptom Documentation" — each under 5 items.

**Bad (merged phases):**

> "Initiation and Continuation Criteria: [combined block]"

**Good:**

> Two separate blocks: "Initiation Criteria" and "Continuation Criteria"

**Bad (missing Tags):**

> "- Patient Age: Extract the patient's age."

**Good:**

> "- Patient Age: Extract the patient's age or date of birth. (Tags: Medical Record, Physician Written Order)"

---

## Check 8 — Payer Scope Mismatch

**Goal:** Criteria content must match the plan category declared in the header.

**What to flag:**

- Medicare-specific language (LCD/NCD references, ABN, "Medicare fee schedule," "CMS") appearing in Commercial or Medicaid blocks
- State-specific Medicaid rules embedded in a generic or multi-state block
- Plan category header says COMMERCIAL but criteria include Medicare-specific clinical thresholds that aren't required by the commercial payer's actual policy
- **Imaging-specific — NCD/LCD conflation:** a criterion sourced from a local MAC's LCD is cited or worded as if it were nationally binding, or a criterion sourced from a national NCD is worded as if a local MAC could narrow or override it. Confirm each citation names the correct source type — and, for LCD-sourced criteria, the specific MAC jurisdiction, not "an LCD" generically.
- **Medicare-specific logic applied to a non-Medicare document, or vice versa:** NCD/LCD/MAC-jurisdiction sourcing pattern used on a Medicaid, MA, or Commercial policy, or a state/plan-jurisdiction pattern used where Medicare's NCD/LCD hierarchy actually applies. Each payer type has its own jurisdiction question — check the payer type first, then apply the matching pattern.
- **State-specific override merged into the default criteria:** a state statute or scope-table redirect identified during drafting was folded into the generic order type instead of written as its own state-scoped segment. Two sub-failures to check for separately: (a) a state statute changed the default rule for every state, not just the one the statute names; (b) a state that the policy explicitly redirects to a separate document was nonetheless given criteria under this order type.

**Bad:**

> Header: Plan Category: COMMERCIAL
> Body includes: "As specified in NCD 220.2..."

**Good:**

> Commercial criteria reference the commercial payer's own Clinical Policy Bulletin, not an NCD or LCD.

**Bad (NCD/LCD conflation):**

> Criterion sourced from a MAC's LCD, cited as: "*Source: NCD 220.2*" — misattributes a local-discretion criterion as nationally binding.

**Good:**

> "*Source: [MAC name] LCD L[number], §Coverage Indications* — this indication is not addressed by NCD 220.2 and is instead governed by local MAC discretion."

**Bad (state override merged into default):**

> Generic "Continuation of Therapy" criterion states "Reauthorization will be for no more than 12 months" for every state, when only Illinois's statute requires a 12-month floor and the payer's own generic policy states 6 months for all other states.

**Good:**

> Default "Continuation of Therapy" segment states the generic 6-month reauthorization. A separate "Illinois — Statutory Reauthorization Override" segment states the 12-month statutory floor, scoped explicitly to Illinois patients meeting the statute's own conditions (e.g., 2+ years of sustained response).

**Bad (redirected state given default criteria anyway):**

> Policy's Application table redirects Ohio to a separate Ohio-only policy, but the drafted order type includes Ohio under the generic diagnosis-specific criteria with no exclusion noted.

**Good:**

> Drafted order type notes: "This order type does not govern Ohio — see [Ohio-specific policy] per the source document's Application table."

---

## Check 9 — Merge Candidates

**Goal:** Identify criteria blocks that are semantically identical but written differently, creating maintenance burden and inconsistency.

**Merge candidate definition:** Two criteria are merge candidates if they express the same requirement but differ only in surface form — not in clinical meaning.

**Surface differences that qualify for merge:**

- Capitalization drift ("AND" vs "and")
- Minor grammatical variation ("Patient has" vs "Patient must have")
- Punctuation ("Patient has COPD." vs "Patient has COPD")
- Numbering style (A/B/C vs 1/2/3)
- Synonymous words ("practitioner" vs "provider", "shall" vs "must")
- Minor word order ("BMI greater than 35" vs "BMI > 35")

**Do NOT flag as merge candidates:**

- Blocks with different thresholds (initial vs. continuation criteria often differ intentionally)
- Blocks for different payer types that happen to look similar (Medicare vs. Commercial baseline)
- Blocks that differ for known customer-specific reasons

**Format for reporting merge candidates** (append below the widget, not inside it):

```
Merge candidate: [short description of what's duplicated]
Appears in: [Block A location] and [Block B location]
Differs by: [specific surface difference]

Version A ([location]):
> [exact text]

Version B ([location]):
> [exact text]

Recommended canonical:
> [proposed unified text]
```

---

## Check 10 — Non-Qualification Content (over-generation)

**Goal:** Every criterion must test a fact about the patient's clinical chart. Flag as **POLICY** any criterion that is claims-adjudication or administrative logic — reviewers delete these even when the policy states them verbatim.

**Flag each criterion in these categories, with the fix "delete this criterion":**

- **Order/requisition paperwork mechanics** — referring-order timing rules, required order elements (NPI, signature, dating), state forms
- **Prior authorization / approval / billing** — prior-auth process, approval or authorization periods, reimbursement, claim submission, fee-schedule or CPT/HCPCS coverage statements, modifier rules
- **Enrollment / eligibility** — program-enrollment rules ("enrolled in Florida Medicaid on the date of service")
- **Code bundling** — mutual-exclusion or same-day/month/period code-combination rules ("not both", NCCI-style edits). Distinguish this from a genuine Code Dependency (Check 11) — bundling is a billing edit; a Code Dependency is a clinical condition on another code's outcome.
- **Place-of-service / residency** — inpatient-vs-outpatient setting rules, unless the policy makes the setting a clinical coverage condition for the requested code
- **Facility and equipment certification** — facility accreditation, unit FDA premarket-approval status, or technologist certification requirements, unless tied to a patient-specific safety decision (Device Safety Gate, Check 12)
- **Radiologist workflow / turnaround** — report turnaround time, read assignment, or interpretation-billing rules, unless tied to an actual clinical decision point
- **Generic documentation boilerplate** — "medical records support medical necessity", "service does not duplicate another service", "an individualized plan of care exists", record-retention or reorder-log requirements

**Do NOT flag (these are genuine qualification criteria):**

- Documentation tied to a specific clinical fact (signed order or clinical note within a stated window; documentation of a specific symptom, measurement, prior-test outcome, or trial-and-failure)
- Frequency/interval limits and clinical timing rules for the requested code
- Convenience/preference exclusions and age-conditional medical-necessity standards
- Diagnoses, clinical findings, functional limitations, objective thresholds
- Genuine Code Dependencies, Contraindication Gates, and Device Safety Gates (see Checks 11–12) — these are patient-clinical conditions, not administrative logic, even though they reference another code or an equipment/implant status

**Bad (must be flagged):**

> "A completed Standard Written Order was communicated to the supplier before the claim was submitted."
> "The patient is enrolled in the Florida Medicaid program on the date of service."

**Good (must NOT be flagged):**

> "Patient has a face-to-face evaluation, signed by the treating practitioner, conducted within 6 months prior to the initial order."
> "The ordered quantity of T4543 does not exceed 300 per month."

**Also under this check — cap-semantics fidelity (flag as HIGH):**

- A hard policy interval/cap weakened with an invented escape hatch ("OR the medical record documents medical necessity for an earlier repeat study" when the policy grants no such path)
- A policy-overridable interval hardened into an absolute cap (documented-exception path dropped)
- A numeric range missing one of its bounds
- A vessel/region/device compatibility list with entries the policy does not name
- Duplicate criteria (exact or near-duplicate)

---

## Check 11 — Code Dependency Validity

**Goal:** Every criterion whose medical necessity hinges on another CPT/HCPCS code's outcome must name that code explicitly and state the required status unambiguously.

**What to look for:**

- Does the criterion name a specific other CPT/HCPCS code, or only describe the dependency in vague prose ("after the other study fails")?
- Is the required status stated as QUALIFIED or DISQUALIFIED/RULED OUT — not left to be inferred?
- Does the named code actually exist in this order type or a stated related order type? A dependency pointing to a code that was never classified anywhere is unverifiable.
- Is a Base Procedure Dependency (add-on code, Classification Step 4a) distinguished from a Sequential/Outcome Dependency (Classification Step 4b)? An add-on code's ENTIRE criterion should be the dependency; an outcome-dependent code's dependency should be ONE sub-item within its own broader indications.
- Is a Dual-Test Rule ("only one of two studies covered absent both being necessary") written as a Code Dependency against the other modality's code, not as vague "coordination" language?

**Bad (vague, unverifiable):**

> "This study may be covered as a follow-up when the initial test doesn't work."

**Good (explicit code, explicit status):**

> "Add-On MRA for Runoff Vessel Identification: Patient meets both of the following:
> 1. A prior contrast angiography (CPT 75710) was performed and was unable to identify a viable runoff vessel for bypass
> 2. Exploratory surgery is not considered a reasonable course of action for this patient"

**Bad (add-on dependency buried as a sub-item instead of being the whole criterion):**

> "Contrast Administration Add-On: Patient has a documented allergy history reviewed.
> 1. Base MRI code is qualified."

**Good:**

> "Base Procedure Dependency: This code is covered only when CPT [base code] ([base code description]) is independently qualified for this patient. This code has no independent clinical indication of its own."

---

## Check 12 — Contraindication and Device Safety Gate Placement

**Goal:** Absolute exclusions and implant-safety branches must be structured so they apply everywhere they should, and so a safety checklist can't collapse into one unreviewable field.

**What to look for:**

- Is each absolute contraindication (pregnancy, incompatible implant, excluded anatomy target) written as its own named criterion, evaluated ahead of positive indications — not nested inside a single indication's AND-chain where it would only block that one pathway?
- If the policy states multiple contraindications, is each one its own criterion rather than merged into one block?
- For a Device Safety Gate (e.g., MRI-conditional pacemaker/ICD pathway): is the FDA-labeled branch separated from the non-labeled branch? Within the non-labeled branch, is every discrete checklist requirement (field strength, lead integrity, each individual facility-checklist item) its own numbered sub-item — not one flowing sentence?

**Bad (contraindication nested inside one pathway only):**

> "Head/Neck MRA Indication: Patient has a condition of the head/neck for which surgery is anticipated, AND patient is not pregnant, AND [vessel/condition criteria]." — pregnancy exclusion won't apply to any other pathway (peripheral, abdomen/pelvis, chest) for this same patient.

**Good:**

> Separate criterion, evaluated first: "Contraindication — Viable Pregnancy: Patient is not currently pregnant with a viable pregnancy." Applies across every region/modality pathway for this code.

**Bad (bundled safety checklist):**

> "Device Safety: If the device isn't FDA-labeled, the facility must assess the patient, discuss risks, interrogate and reprogram the device, have a qualified provider supervise, monitor the patient, have ACLS present, and reinterrogate before discharge." — one block, will generate one extraction field for eight distinct requirements.

**Good:**

> Eight separate numbered sub-items, one requirement each, under a "Device Safety — Non-Labeled Pathway" criterion.
