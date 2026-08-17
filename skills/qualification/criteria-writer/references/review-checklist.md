# Criteria Review Checklist

Detailed reference for all 10 checks run during a criteria review. Each check includes the rule, what to look for, and bad vs. good examples.

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

- Medicare-specific language (LCD references, ABN, "Medicare fee schedule," "CMS," "DMEPOS") appearing in Commercial or Medicaid blocks
- State-specific Medicaid rules embedded in a generic or multi-state block
- Plan category header says COMMERCIAL but criteria include Medicare clinical thresholds (e.g., AHI ≥ 15) that aren't required by the commercial payer's actual policy

**Bad:**

> Header: Plan Category: COMMERCIAL
> Body includes: "As specified in LCD L33718..."

**Good:**

> Commercial criteria reference the commercial payer's own benefit document, not an LCD.

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

- **Order/CMN/SWO paperwork mechanics** — CMN or Standard Written Order timing ("dated within 21 days", "less than 12 months old", "communicated to supplier before claim submission"), required order elements (NPI, signature, dating), state forms
- **Prior authorization / approval / billing** — prior-auth process, approval or authorization periods, reimbursement, claim submission, fee-schedule or CPT/HCPCS coverage statements, modifier rules
- **Enrollment / eligibility** — program-enrollment rules ("enrolled in Florida Medicaid on the date of service")
- **Code bundling** — mutual-exclusion or same-day/month/period code-combination rules ("not both", NCCI-style edits)
- **Place-of-service / residency** — nursing-facility / hospice / inpatient setting rules, unless the policy makes the setting a clinical coverage condition for the requested code
- **Generic documentation boilerplate** — "medical records support medical necessity", "service does not duplicate another service", "an individualized plan of care exists", record-retention or reorder-log requirements

**Do NOT flag (these are genuine qualification criteria):**

- Documentation tied to a specific clinical fact (signed face-to-face evaluation within a stated window; documentation of a specific symptom, measurement, or trial-and-failure)
- Quantity limits and clinical frequency rules for the requested code
- Convenience/preference exclusions and age-conditional medical-necessity standards
- Diagnoses, clinical findings, functional limitations, objective thresholds

**Bad (must be flagged):**

> "A completed Standard Written Order was communicated to the supplier before the claim was submitted."
> "The patient is enrolled in the Florida Medicaid program on the date of service."

**Good (must NOT be flagged):**

> "Patient has a face-to-face evaluation, signed by the treating practitioner, conducted within 6 months prior to the initial order."
> "The ordered quantity of T4543 does not exceed 300 per month."

**Also under this check — cap-semantics fidelity (flag as HIGH):**

- A hard policy cap weakened with an invented escape hatch ("OR the medical record documents medical necessity for a higher quantity" when the policy grants no such path)
- A policy-overridable cap hardened into an absolute cap (prior-auth or documented-exception path dropped)
- A numeric range missing one of its bounds
- A device/code compatibility list with entries the policy does not name
- Duplicate criteria (exact or near-duplicate)
