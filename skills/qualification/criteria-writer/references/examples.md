# Criteria Examples

Real Tennr criteria in the exact format used in the system. Study the structure carefully — the nesting, tagging, and inline extraction pattern are all load-bearing.

---

## The Real Format

```
# [Service Line Name]

Service Line: [name]
Plan Category: [MEDICARE / MEDICAID / COMMERCIAL / etc.]

## Doc Criteria

### [Document Type Label]

**Name:** [reusable name for this doc block]
**Description:** [type label, e.g., Physician Written Order]
- [Extraction Field Name]: [extraction instruction]
- [Extraction Field Name]: [extraction instruction]

## Primary Products

### [HCPCS Code]

**Description:** [code long description]

- [Criteria Name]: [Left-side criteria statement — what insurance requires, in plain English with numbered/lettered sub-items and explicit AND/OR logic]

  - [Extraction Field Name]: [Right-side instruction — how/where to find this in the documents] (Tags: [Document Type 1, Document Type 2])

  - [Next Extraction Field]: [instruction] (Tags: [Document Type])

- [Next Criteria Name]: [criteria statement]

  - [Extraction Field Name]: [instruction] (Tags: [Document Type])

## Accessory Products

### [HCPCS Code]
**Description:** [description]
```

**Critical structure rules:**

- Doc Criteria come first and define the standard document-level extractions (prescription fields, F2F fields, sleep study fields, etc.)
- Each product-level criteria is a single bullet with a name and statement
- Extraction fields are indented 2 spaces under the criteria they belong to
- Every extraction ends with `(Tags: ...)` naming which document type(s) to search
- Tags must match the document type names defined in Doc Criteria

---

## Example 1: E0601 — CPAP Device (Medicare, Initial Coverage)

```
# E0601 - Initial Coverage

Service Line: Positive Airway Pressure (PAP) Devices
Plan Category: MEDICARE

## Doc Criteria

### Physician Written Order

**Name:** PAP RX without Frequency/Quantity
**Description:** Physician Written Order
- Prescribed Item: Description or HCPC code is present
- Date of Prescription: Extract the date on which the prescription was written, signed, or re-certified. The date may be formatted in various formats such as MM/DD/YYYY, DD/MM/YYYY, or YYYY-MM-DD. If the recertification date is present and there is not a signature date, use the recertification date as prescription date. This is usually towards the top of the page or next to the doctor's signature. This cannot come from the fax cover sheet. The signature date should take priority.
- Practitioner's Name or NPI: Find either the name or the National Provider Identifier (NPI) of the practitioner who wrote the prescription. This information is usually located near the signature or in the header of the document.
- Practitioner's Signature: Locate the Practitioner's signature on the prescription document. This may be hand-written or electronic, typically found towards the end or bottom of the document. For handwritten signatures, look for cursive, or stylized, or looped handwriting near "physician signature," "prescriber signature," or "M.D." For electronic signatures look for: Signed/Authenticated by, Electronic Signature, signature date, Verified by, Authenticated by, Authorized by, Digital Signature, Electronically Approved, Finalized by
- PAP Pressure Settings: Extract the PAP pressure settings, which may be listed as a specific value or range. Look for associated terms like 'pressure setting,' 'cm H₂O,' and 'titration.'
- Patient Name: Extract the name of the patient as it appears on the prescription document. This is typically located at the top or within the patient details section.

### Medical Record

**Name:** Face to Face
**Description:** Medical Record
- Practitioner Signature on Face to Face Encounter: Find and extract the signature of the practitioner on the documentation of the face-to-face encounter.
- Date of Practitioner Signature on Face to Face Encounter: Extract the date of the practitioner's signature on the documentation of the face-to-face encounter. If not available, use the date of the face-to-face encounter itself as reference.
- Face-to-Face Evaluation Type: Indicate whether the face-to-face evaluation was conducted via Telehealth, Televisit, or in person. In Person: Qualifies. No mention of Telehealth/Televisit: Qualifies. Telehealth/Televisit mentioned: Qualifies, as long as the note does not explicitly state that only audio or only telephone was used. Telephone encounters are not acceptable.

### Baseline Sleep Study

**Name:** Sleep Study
**Description:** Baseline Sleep Study
- Practitioner Signature: Locate the signature of the practitioner on the sleep study document. The document could say electronically signed by and this would qualify.
- Signature Date by Practitioner: Find the date associated with the practitioner's signature on the sleep study document.
- Hypopnea Scoring: Determine the oxygen desaturation standard used for scoring hypopneas. Look for mentions of a 4% oxygen desaturation criteria or references to AASM 1B guidelines.

## Primary Products

### E0601

**Description:** Continuous positive airway pressure (CPAP) device

- Medicare Sleep Test AHI/RDI Criteria: To qualify, the patient must have a sleep test that meets either Requirement 1 OR Requirement 2 below, using an AHI, pAHI, or conditionally RDI or REI.

Index Selection Rules:
• pAHI should be treated as equivalent to AHI.
• If both AHI and pAHI are present, either may be used, but do not combine them.
• AHI or pAHI should be used when available.
• If neither is available, REI or RDI may be used with the following conditions:
For home sleep studies: REI or RDI may be used even if RERA is not explicitly documented.
For in-lab sleep studies: RDI may only be used if RERA is explicitly documented and can be excluded. If RERA cannot be isolated, default to AHI or pAHI.

Clinical Qualification (once appropriate index is selected):
1. Selected index ≥ 15 events per hour AND total apneas + hypopneas ≥ 30
OR
2. Selected index is between 5 and 14.9 events per hour AND total apneas + hypopneas ≥ 10 AND one of the following (2A, 2B, or 2C):
2A. Excessive daytime sleepiness, impaired cognition, mood disorders, OR insomnia
2B. Epworth Sleep Scale (ESS) score above 11
2C. Hypertension, ischemic heart disease, OR history of stroke

If the total number of events is not available, calculate: selected index × total sleep time (in hours).

  - RERA Documentation: Identify any explicit mention of Respiratory Effort-Related Arousals (RERA) in the sleep test documentation. Note if RERA is documented as present or absent. (Tags: Baseline Sleep Study)

  - AHI, pAHI, RDI, or REI Values: Identify the type and value of the index used in the sleep test. Look for terms like AHI, pAHI, REI, or RDI. If both AHI and pAHI are present, either may be used. (Tags: Baseline Sleep Study)

  - Total Number of Apnea + Hypopnea Events: Find the total number of apnea and hypopnea events recorded during the sleep test. (Tags: Baseline Sleep Study)

  - Total Sleep Duration: Find the total sleep duration recorded during the sleep test. Often listed as "Total Sleep Time" or "Total Sleep Recording Time" in minutes or hours. (Tags: Baseline Sleep Study)

  - Clinical Conditions: Identify any documented clinical conditions: excessive daytime sleepiness, impaired cognition, mood disorders, insomnia, hypertension, ischemic heart disease, history of stroke, or Epworth Sleep Scale (ESS) score. (Tags: Medical Record)

- OSA Signs and Symptoms Assessment: Assessment of OSA signs and symptoms — excessive daytime sleepiness, loud snoring, observed apneas, morning headaches, abrupt awakenings by gasping or choking — must be documented. Notes indicating a history of sleep apnea or OSA also qualify. Physician must have reason to believe patient has sleep apnea or OSA.

  - OSA Signs and Symptoms: Identify OSA-related signs and symptoms. Look for 'excessive daytime sleepiness,' 'loud snoring,' 'observed apneas,' 'morning headaches,' 'abrupt awakenings by gasping or choking,' or related symptoms. (Tags: Medical Record)

  - History of Sleep Apnea or OSA: Extract mentions of a history of sleep apnea or OSA, including past therapy indicating OSA management. (Tags: Medical Record)

  - OSA Diagnostic Codes: Identify any diagnostic codes related to OSA, specifically G47.33. (Tags: Medical Record)

- OSA Encounter and Prescription Timing: Face-to-face encounter that mentions suspicion of OSA must be dated prior to the sleep study. If encounter and sleep study are on the same day, assume encounter is prior.
AND
The prescription must be dated after the sleep study. If prescription and sleep study are on the same day, assume prescription is after.

  - Date of Face-to-Face Encounter for OSA Suspicion: Extract the date of the face-to-face encounter that mentions suspicion of OSA. If encounter and sleep study are on the same day, assume encounter is prior. (Tags: Medical Record)

  - Date of Sleep Study: Find the date on which the sleep study took place. (Tags: Baseline Sleep Study)

  - Date of Prescription: Extract the date of the prescription. If prescription and sleep study are on the same day, assume prescription is after. (Tags: Physician Written Order)

- Hypopnea Scoring Criteria: Hypopneas must be scored using a 4% oxygen desaturation standard OR AASM 1B guidelines. Accept if any of the following are met:
- The report states hypopneas were scored using 4% desaturation
OR
- The report was scored using 3% but includes a 4% value in parentheses or as an alternate value
OR
- The report states scoring followed AASM 1B guidelines

  - Desaturation Standard Used for Hypopneas: Identify the oxygen desaturation standard used for scoring hypopneas. Look for "4% desaturation" or "AASM 1B guidelines." If "3% desaturation" is used, check for any reference to a 4% value in parentheses. (Tags: Baseline Sleep Study)

  - 4% AHI Value: Extract the AHI value associated with 4% desaturation standard if mentioned anywhere in the report, especially if primary scoring uses 3% desaturation. May be in parentheses or listed as an alternate value. (Tags: Baseline Sleep Study)
```

---

## Example 2: E2103 — CGM Device (Medicare)

```
# E2103 - Non-Adjunctive/Non-Implanted Continuous Glucose Monitor or Receiver

Service Line: Continuous Glucose Monitoring (CGM)
Plan Category: MEDICARE

## Doc Criteria

### Physician Written Order

**Name:** RX without frequency/quantity requirements
**Description:** Physician Written Order
- Prescribed Item: Description or HCPC code is present
- Date of Prescription: Extract the date on which the prescription was written, signed, or re-certified. If the recertification date is present and there is not a signature date, use the recertification date. The signature date should take priority.
- Practitioner's Name or NPI: Find either the name or the NPI of the practitioner. Usually located near the signature or in the header.
- Practitioner's Signature: Locate the Practitioner's signature. For handwritten signatures, look for cursive or stylized handwriting near "physician signature" or "prescriber signature." For electronic signatures look for: Signed/Authenticated by, Electronic Signature, Verified by, Authenticated by, Authorized by, Digital Signature, Electronically Approved, Finalized by
- Patient Name: Extract the name of the patient. Typically located at the top or within the patient details section.

### Medical Record

**Name:** Face to Face
**Description:** Medical Record
- Practitioner Signature on Face to Face Encounter: Find and extract the signature of the practitioner on the face-to-face encounter documentation.
- Date of Practitioner Signature on Face to Face Encounter: Extract the date of the practitioner's signature. If not available, use the date of the encounter itself.
- Face-to-Face Evaluation Type: In Person: Qualifies. No mention of Telehealth/Televisit: Qualifies. Telehealth/Televisit: Qualifies unless explicitly audio-only or telephone-only.

## Primary Products

### E2103

**Description:** Non-adjunctive, non-implanted continuous glucose monitor or receiver

- Diabetes Diagnosis Required: Patient must have a diagnosis of diabetes.

  - Diabetes Diagnosis: Find and extract one of the following diabetes diagnosis codes: E08.xx, E09.xx, E10.xx, E11.xx, E13.xx, or O24.xx (gestational diabetes). [Full ICD-10 code list applies per LCD.] (Tags: Medical Record)

- CGM Prescription Criteria: The beneficiary meets criteria A OR B OR C below:

A. The beneficiary is insulin-treated
OR
B. The beneficiary has a history of problematic hypoglycemia with recurrent (more than one) level 2 hypoglycemic events (glucose <54 mg/dL) that persist despite multiple attempts to adjust medication(s) and/or modify the diabetes treatment plan.
OR
C. A history of one level 3 hypoglycemic event (glucose <54 mg/dL) characterized by altered mental and/or physical state requiring third-party assistance for treatment.

  - Beneficiary is insulin-treated: Documentation that shows the patient is using insulin. (Tags: Medical Record, Physician Written Order)

  - Level 2 hypoglycemic events: Documentation of recurrent (more than one) level 2 hypoglycemic events (glucose <54 mg/dL) that persist despite multiple attempts to adjust medication(s) or modify the diabetes treatment plan. (Tags: Medical Record, Physician Written Order)

  - Level 3 hypoglycemic event: A history of one level 3 hypoglycemic event (glucose <54 mg/dL) characterized by altered mental and/or physical state requiring third-party assistance for treatment. (Tags: Medical Record, Physician Written Order)
```

---

## Example 3: A4311 — Urological Catheter Supply (Medicare)

This example shows how quantity/frequency criteria work, and how to write permanence criteria with multiple sub-indicators.

```
# Urology Supplies (excerpt — A4311)

Service Line: Urological Supplies
Plan Category: MEDICARE

## Primary Products

### A4311

**Description:** Insertion tray without drainage bag with indwelling catheter, Foley type, 2-way latex with coating

- Permanent Urinary Incontinence/Retention: Medical records must support that the beneficiary has permanent urinary incontinence OR permanent urinary retention. All of the following conditions must be satisfied:

A. Definition of Permanence: The diagnosis must reflect a permanent condition — not simply a permanent need for catheterization. Permanence must be attributed to the diagnosis itself.

B. Timing: The condition must be present for more than three months OR documentation must indicate it is not expected to be corrected within the next three months.

C. Supporting Documentation Indicators (one or more must be present):
- Onset of diagnosis is greater than three months ago
- Diagnosis is noted as established with follow-up exceeding three months
- Condition is explicitly documented as permanent, chronic, longstanding, lifelong, persistent, or indefinite
- Condition is described as "not expected to improve" or "not amenable to surgical or medical correction"
- Note includes a specific chronic condition associated with permanent retention/incontinence (e.g., spinal cord injury, multiple sclerosis)
- Patient history includes multiple years of urinary retention or incontinence
- Provider documents ongoing use of catheterization with no expectation of reversal

D. Prognosis Irrelevant: If the diagnosis of permanent urinary incontinence or retention is established, the overall prognosis does not affect this criterion.
```

---

## Key Patterns to Learn

1. **Doc Criteria** defines the standard document types (Rx, F2F, Sleep Study, Medical Record) and their reusable extraction fields. These are referenced by Tags on all code-specific extractions.

2. **Extraction fields nest directly under their criteria** — not in a separate section. Two spaces of indentation, then `- Field Name: instruction (Tags: ...)`.

3. **Tags are always document type names** that match the headers in Doc Criteria exactly.

4. **Criteria naming**: Each clinical criteria block has a descriptive name (bold, followed by colon), then the requirements. Sub-items use 1/2/3 or A/B/C with explicit AND/OR separators.

5. **Extraction field names should be specific and descriptive** — they appear as column headers in the Tennr UI and in audit trails. "Diabetes Diagnosis" is better than "Diagnosis." "Date of Face-to-Face Encounter for OSA Suspicion" is better than "F2F Date."

6. **Conditional criteria** (like "only evaluate if quantity > 1") are written on the left side. The right side extractions still extract the raw data values — they don't make the conditional decision.

7. **No Doc Criteria block needed** when all criteria are medical-record only with no standard prescription.

8. **Extraction instructions should be generous with synonyms** — "CPAP," "Auto-PAP," "E0601," "continuous positive airway pressure" are all worth including because documents vary wildly.
