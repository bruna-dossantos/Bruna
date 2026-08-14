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
- Use the exact verbatim language from the policy source — do not paraphrase or simplify
- Bold key terms and conditions
- Italicize document-type indicators (_Found in: Prescription_, _Found in: Medical Records_)
- Specify signature and date requirements when the policy demands them
- Include the specific provider type when relevant (physician vs. NP/PA vs. RT)
- Number each distinct requirement so the right side can reference them
- Include a verbatim policy quote with page/section reference under each criterion block

### Don't:

- ❌ Include reasoning or "if-then" decision logic on the left side
- ❌ Write extraction instructions on the left side ("Check if...", "Look for...")
- ❌ Bundle too many requirements into one long block (breaks extraction generation)
- ❌ Use vague language ("appropriate documentation", "sufficient evidence")
- ❌ Reference competitor products or brand names that don't apply to this customer
- ❌ Include criteria that Medicare doesn't actually require (e.g., edema for lymphedema)
- ❌ Mix Medicare and non-Medicare logic in the same criteria block
- ❌ Use "member" or "beneficiary" — always use "patient"

### Prescription fields — always include all of these when a prescription is required:

1. Item name or HCPCS code (with synonyms)
2. Practitioner's signature
3. Patient name
4. Practitioner's name or NPI
5. Date (with logic: signature date > recertification date > most recent date)
6. Any additional fields the policy requires (e.g., PAP pressure settings, quantity)

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

- **SWO / Prescription**: Standard Written Order. Must be signed and dated. Contains item name/code, patient name, prescriber info.
- **Face-to-Face (F2F)**: In-person or qualifying telehealth evaluation. Must be signed and dated. Telehealth, televisit, "shown up," "present," "seen" are acceptable. Telephone-only is NOT acceptable.
- **Progress Notes / LMN**: Letter of Medical Necessity or clinical progress notes from the treating practitioner.
- **Sleep Study**: Polysomnography (PSG) or home sleep study. Must be signed and dated. Used for PAP equipment.
- **Blood Gas / ABG**: Arterial or capillary blood gas results. Used for oxygen and ventilator equipment.
- **Diagnostic Testing**: Lab results, imaging, test reports referenced in the policy.

---

## Payer-Specific Rules

### Medicare:

- Use Medicare LCD as the primary source. Most DME codes have an LCD from Noridian, CGS, or another MAC.
- Medicare is the strictest baseline — MA and Medicaid may be looser.
- Do NOT include state-specific Medicaid requirements in a Medicare order type.

### Medicare Advantage (MA):

- MA plans must follow Medicare rules at minimum, but individual plans may add requirements.
- When writing MA criteria, note: "Follows Medicare baseline unless plan-specific policy overrides."

### Medicaid:

- State-specific. Criteria vary significantly by state. If writing Medicaid criteria, confirm which state.
- Don't conflate Medicaid with Medicare Advantage or Medicare — these are distinct.

### Commercial:

- Typically most permissive. Often prescription-only for many DME codes.
- Confirm whether the customer has a specific payer contract requirement.

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
9. **Wound Count Modifiers (A1–A9)** — Do NOT include wound count modifiers (A1–A9 or similar) in criteria. These are billing/claim modifiers, not qualification criteria. Do not add them to the prescription fields, extraction fields, or Doc Criteria. Leave modifier handling to the billing workflow.
10. **Initiation vs. Continuation (and any similar breakouts)** — If the policy distinguishes between Initiation and Continuation criteria — or any other named phases or conditions (e.g., Initial vs. Renewal, Acute vs. Chronic, Trial vs. Ongoing) — write each as a **separate criteria segment**, never combined into one block. Each segment gets its own named criteria entry (e.g., "Initiation Criteria" and "Continuation Criteria") so Tennr can evaluate them independently.
11. **Conditional logic on the right side** — Any if-then or conditional logic on the extraction side is always a HIGH severity defect. Never add it; always remove it.
12. **Exclusionary language on the right side** — Any "Do NOT accept", "Only X qualifies", or "Reject if" language on the extraction side is always a HIGH severity defect. Never add it; always remove it.
13. **Paraphrased policy language** — All criteria text must use exact verbatim wording from the source policy. Paraphrased or simplified versions introduce inaccuracies and must be corrected against the source document.
14. **Wrong terminology** — "Member" or "beneficiary" in any output. Always replace with "patient."
15. **Parenthetical notes** — Any note formatted as `(Note: ...)` must be converted to an inline sentence (Option A style).
