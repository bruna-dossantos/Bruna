# Classification Decision Tree

Use this decision tree to classify each remaining HCPCS code. Work through it top to bottom — the first match wins.

---

## 1. Is the code explicitly noncovered?

Check the LCD and Policy Article for language like:

- "[Code] will be denied as not reasonable and necessary"
- "[Code] is noncovered under the DME benefit"
- "[Code] offers no proven clinical advantage"
- "[Code] is a convenience item"

**If yes → Classification: NONCOVERED**

Examples from the Nebulizer LCD:

- A7008 (prefilled disposable large vol neb) — noncovered because it's a "convenience item"
- E0575 (large vol ultrasonic neb) — denied, "no proven clinical advantage over a pneumatic compressor"

---

## 2. Is the code named in the Coverage Indications section with clinical criteria?

Read the LCD's "Coverage Indications, Limitations, and/or Medical Necessity" section. Look for paragraphs that explicitly name the code alongside clinical requirements.

Patterns to look for:

- "[Code] is considered for coverage when it is reasonable and necessary to [clinical scenario]"
- "A [device type] ([Code A], [Code B]) and related [equipment] ([Code C]) are considered for coverage when..."
- "[Code] is covered for the same indications as [other section reference]"

**If the code is named with clinical criteria AND a completed code shares the same criteria → Classification: COPY FROM [completed code]**

**If the code is named with clinical criteria AND no completed code shares the same criteria → Classification: NEEDS ORIGINAL CRITERIA**

How to determine if criteria match: the LCD will often group codes together in the same coverage paragraph. If the remaining code appears in the same paragraph as a completed code, they share criteria. Also check if the LCD says "covered for the same indications" — that's an explicit pointer.

Examples:

- A7017 shares the same paragraph as A7007 ("A large volume nebulizer (A7007, A7017)... are considered for coverage when...") → Copy from A7007
- A7006 is named alongside E0565/E0572 for pentamidine administration → Copy from E0565

---

## 3. Does the code have its own ICD-10 group assignment?

Check the Policy Article's "ICD-10-CM Codes that Support Medical Necessity" section. Each group header specifies which HCPCS codes it covers, e.g., "For HCPCS codes A4619, E0565, E0572."

If a remaining code appears in a group header, it has a defined coverage pathway — even if the LCD text didn't give it a long paragraph.

**If the code shares an ICD-10 group with a completed code → Classification: COPY FROM [completed code that shares the group]**

**If the code has its own ICD-10 group but no completed code shares it → Classification: NEEDS ORIGINAL CRITERIA**

Examples:

- A4619 shares Group 1 with E0565 and E0572 → Copy from E0565
- A7525 shares Group 2 with A7015 → Copy from A7015

---

## 4. Does the code only appear in the accessories table?

If the code wasn't found in steps 1-3 — not noncovered, not in the criteria text, not in any ICD-10 group — but IS listed in the LCD's accessories table (mapping compressors/generators to their related accessories):

**Classification: ACCESSORY ONLY**

Record:

- Which parent equipment code(s) it's listed under
- The replacement frequency from the qty limits table (if present)

Accessory-only codes have no independent clinical criteria. Their coverage is derivative — they're covered when the parent equipment is covered and the individual accessory is reasonable and necessary. The criteria should state this dependency rather than duplicating the parent's clinical criteria.

Examples:

- A7012 (water collection device) — only in accessories table for E0565 and E0585
- A7016 (dome and mouthpiece) — only in accessories table for E0574
- E1372 (immersion heater) — only in accessories table for E0565 and E0585

---

## 5. Code not found anywhere in the policy

If the code doesn't appear in the LCD, the Policy Article, the accessories table, or anywhere else in the policy documents:

**Classification: OUT OF SCOPE**

This code isn't governed by this LCD. Don't classify it — note it as out of scope and move on. The user may need to find a different LCD or policy source for it.

---

## Edge cases

### Code appears in both the accessories table AND criteria text

The criteria text wins. If the LCD names a code with clinical criteria, it has explicit criteria — even if it also appears in the accessories table. Many accessories are listed in both places.

### Code appears in criteria text but only as part of a billing rule

Some codes are mentioned in the Policy Article's coding guidelines purely for billing purposes (e.g., "E0580 should only be billed when the nebulizer is used with a beneficiary-owned oxygen system"). Billing rules are NOT clinical criteria. If the code is only mentioned in billing context, check whether it has its own ICD-10 group or appears in the accessories table — classify accordingly.

### Code has criteria but it's a subset of another code's criteria

Some codes have narrower criteria than a related completed code (e.g., E0574 is only for treprostinil, while E0570 covers many drugs). Don't duplicate from a broader code — the criteria would be wrong. These need original criteria or at minimum careful manual adjustment after copying.

### Same code appears with different qty limits depending on context

Some codes have conditional qty limits (e.g., A7005 is "1/6 months" normally but "1/3 months with K0730"). Capture all applicable qty limits and note the conditions.

---

## Quick reference: classification summary

| Step | Check                                                 | Result                        |
| ---- | ----------------------------------------------------- | ----------------------------- |
| 1    | Explicitly noncovered?                                | → NONCOVERED                  |
| 2    | Named in Coverage Indications with clinical criteria? | → COPY FROM or NEEDS ORIGINAL |
| 3    | Has own ICD-10 group assignment?                      | → COPY FROM or NEEDS ORIGINAL |
| 4    | Only in accessories table?                            | → ACCESSORY ONLY              |
| 5    | Not found anywhere?                                   | → OUT OF SCOPE                |
