# Classification Decision Tree — Imaging

Use this decision tree to classify each remaining CPT/HCPCS imaging code. Work
through it top to bottom — the first match wins. This replaces the DME/LCD
accessory-table tree with the structure imaging policies actually use: national
vs. local sourcing, base-procedure add-ons, and cross-code outcome dependencies.

---

## 0. Which source/jurisdiction governs?

Before classifying the code's coverage logic, determine which document and
jurisdiction actually control it. Do this once per code, before Step 1. **The
specific check depends on the payer — do not default to the Medicare pattern
for a non-Medicare document.**

**If the payer is traditional Medicare (fee-for-service):**
- Check `https://www.cms.gov/medicare-coverage-database/` for a **National
  Coverage Determination (NCD)** covering this modality (e.g., NCD 220.2 for
  MRI/MRA).
- If an NCD exists and names this code's modality/indication, the NCD
  controls. Only fall through to an LCD for indications the NCD explicitly
  leaves to local discretion (commonly stated as "all other uses... eligible
  for coverage through individual local MAC discretion").
- If no NCD exists, or the NCD doesn't address this code's modality, proceed
  to an LCD search **and name the specific MAC jurisdiction** (Noridian, CGS,
  Palmetto GBA, or another MAC) — never cite "an LCD" generically, since LCDs
  vary by jurisdiction.

**If the payer is Medicaid:** identify the specific STATE Medicaid program
that governs. Many MCOs publish one umbrella coverage document spanning
several states at once, with state-specific statutory carve-outs layered on
top — see the state-callout check below. A rule sourced from one state's
Medicaid program does not apply to a different state's patient even under the
same MCO.

**If the payer is Medicare Advantage or Commercial/Marketplace:** identify the
specific plan/product. MA plans and commercial products from the same
underlying payer are not interchangeable — each can carry its own criteria on
top of (or instead of) a shared baseline.

**Regardless of payer, scan for state-specific callouts every time:**
- A scope/redirect table sending specific states to an entirely separate
  policy document. If found, this order type does NOT govern that state —
  flag it as excluded rather than writing criteria for it.
- An Appendix or "State Specific Information" section citing a state statute
  that overrides part of the generic criteria (most commonly reauthorization/
  duration periods, or a legislatively-mandated diagnosis) for that state
  only. If found, classify it as its own separate state-scoped variant — never
  blend it into the generic classification for every other state.

**Record which source and jurisdiction govern** — this determines how you
cite every criterion drafted from Steps 1–5 below, and whether the code's
criteria are universal within this order type or scoped to a specific
jurisdiction/state/plan.

---

## 1. Is the code explicitly noncovered?

Check the governing NCD/LCD and any supplementing Policy Article for language
like:

- "[Code] is non-covered" / "will be denied as not reasonable and necessary"
- "[Indication] is not considered reasonable and necessary within the meaning
  of section 1862(a)(1)(A) of the Act"
- "[Code] is contraindicated for [population/condition]"

**If yes → Classification: NONCOVERED**

Examples from NCD 220.2 (MRI/MRA):

- MRI of cortical bone and calcifications — nationally non-covered; "not
  considered reasonable and necessary... therefore non-covered"
- MRI for patients with metallic clips on vascular aneurysms — nationally
  non-covered
- MRI during a viable pregnancy — contraindicated, not merely non-covered; write
  this as a Contraindication Gate (see `SKILL.md`), not an ordinary NONCOVERED
  code, since it's patient-specific rather than code-wide

---

## 2. Is the code named with clinical criteria in the Coverage Indications section?

Read the NCD/LCD's "Indications and Limitations of Coverage" (or equivalent)
section. Look for paragraphs that explicitly name the code's modality/region
alongside clinical requirements.

Patterns to look for:

- "[Modality] is considered medically necessary when used to evaluate
  [clinical scenario]"
- "Currently covered indications include using [modality] for specific
  conditions to evaluate [region A], [region B], and [region C]" — each named
  region is its own branch, not one shared criterion (see Step 2 of `SKILL.md`)
- "[Code] is covered for the same indications as [other section reference]"

**If the code is named with clinical criteria AND a completed code shares the
same criteria → Classification: COPY FROM [completed code]**

**If the code is named with clinical criteria AND no completed code shares the
same criteria → Classification: NEEDS ORIGINAL CRITERIA**

How to determine if criteria match: the policy will often group codes together
in the same coverage paragraph, or the CPT descriptions differ only by an
attribute (with/without contrast, unilateral/bilateral, region scope) that the
policy doesn't independently condition. If the remaining code differs from a
completed code ONLY by that kind of attribute, and the policy states no
additional clinical requirement for it, it likely shares the completed code's
criteria plus a code-differentiation criterion (see `SKILL.md`, "Code
differentiation").

Examples:

- MRA of the chest, thoracic aortic dissection/aneurysm evaluation and MRA of
  the chest, pre-operative dissection evaluation share the same paragraph → copy
  from whichever was completed first, plus the pre/post-op timing distinction
  as its own criterion if the policy states one
- An MRI-with-contrast code sharing all indications with its without-contrast
  sibling, differing only in a contrast-administration criterion → copy the
  base indications, add the contrast-specific criterion fresh

---

## 3. Does the code have its own ICD-10 group assignment?

Check the Policy Article's "ICD-10-CM Codes that Support Medical Necessity"
section (common for CT, PET, and other LCD-governed imaging, less common under
NCDs which tend to use narrative indications instead of ICD-10 groups). Each
group header specifies which CPT/HCPCS codes it covers.

If a remaining code appears in a group header, it has a defined coverage
pathway even if the narrative text didn't give it a long paragraph.

**If the code shares an ICD-10 group with a completed code → Classification:
COPY FROM [completed code that shares the group]**

**If the code has its own ICD-10 group but no completed code shares it →
Classification: NEEDS ORIGINAL CRITERIA**

---

## 4. Does the code depend on another code rather than having independent criteria?

This step replaces the DME accessories-table check. Imaging has **two distinct
dependency patterns** — determine which one applies; they're written
differently (see `SKILL.md`, "Code Dependencies").

### 4a. Structural/bundling dependency — ADD-ON CODE

The code is never billed independently. It only exists in conjunction with a
base procedure code, and has no clinical indication of its own — its coverage
is entirely derivative of the base code's qualification. Look for:

- CPT add-on code descriptors ("each additional...", "List separately in
  addition to code for primary procedure")
- A policy statement that the code is only covered "when performed with" or "as
  part of" a named base procedure
- The code appearing only in a table mapping it to base procedure codes
  (structurally the same role the DME accessories table played), never in its
  own indications paragraph

**If yes → Classification: ADD-ON CODE**

Record:
- The base procedure code(s) it rides on
- Whether the policy states any add-on-specific condition beyond "base code
  qualifies" (e.g., a contrast-administration add-on might still require its
  own documented reason for contrast)

Write the criterion as a Base Procedure Dependency (see `SKILL.md`) — the
entire criterion is the dependency, not a sub-item within a larger block.

### 4b. Sequential/outcome dependency — this code has its OWN criteria, plus a hinge

The code has independent clinical indications of its own, but ONE of its
criteria is conditioned on another code's documented outcome — most often that
another study was already attempted and failed, was inconclusive, or is being
deliberately avoided in favor of this one. Look for:

- "when [other modality] was unable to..." / "if [other study] is
  inconclusive..." / "not indicated when [other code] already qualifies using
  [alternative material/method]"
- Dual-test language ("[Modality A] and [Modality B] are not both indicated...
  unless medical necessity for both is demonstrated") — this is always an
  outcome dependency against the other modality's code

**If yes → Classification: OUTCOME-DEPENDENT**

Record:
- This code's own independent indications (draft normally, per Steps 1–3 above)
- PLUS the specific other CPT/HCPCS code and required status (QUALIFIED or
  DISQUALIFIED/RULED OUT) for the dependent criterion — write this as its own
  numbered sub-item within the relevant criterion, not folded into prose

A code can be OUTCOME-DEPENDENT for one criterion while still being classified
under Step 2 or Step 3 for the rest of its criteria — this step adds a
dependency, it doesn't replace the rest of the classification.

---

## 5. Code not found anywhere in the policy

If the code doesn't appear in the NCD, the LCD, the Policy Article, any ICD-10
group, or any add-on/base-code mapping:

**Classification: OUT OF SCOPE**

This code isn't governed by the policy you're working from. Don't classify it —
note it as out of scope and move on. The user may need to find a different
NCD/LCD or policy source for it, or it may fall entirely to local MAC discretion
via a catch-all provision (common in NCDs' "Other" sections) — note that
distinction if the policy states one.

---

## Edge cases

### Code appears in both an add-on/base-code mapping AND has its own criteria text

The criteria text wins, same as the DME rule. If the policy names a code with
its own clinical criteria, it has independent criteria even if it also appears
in a base-code mapping table — classify as OUTCOME-DEPENDENT (4b) if the
criteria reference another code's status, or as its own independent
classification (Step 2/3) if they don't, rather than as a plain ADD-ON CODE.

### Code appears in criteria text but only as part of a billing rule

Some codes are mentioned in a Policy Article's coding guidelines purely for
billing purposes (e.g., "[code] should only be billed when performed with a
contrast agent from [approved list]"). Billing rules are NOT clinical criteria.
If the code is only mentioned in a billing context, check whether it has its
own ICD-10 group or a base-code mapping — classify accordingly.

### Code has criteria but it's a narrower subset of another code's criteria

Some codes have narrower criteria than a related completed code (e.g., an MRA
of a single named vessel is narrower than a general "MRA of the head and neck"
code covering several vessels). Don't duplicate from the broader code without
adjustment — the criteria would over-qualify. These need original criteria, or
at minimum the completed code's criteria narrowed to the specific vessel/region
this code actually covers.

### Same code's criteria differ by region or modality context

This replaces the DME "different qty limits by context" edge case. Some codes
have genuinely different qualifying criteria depending on anatomic region (MRA
of head/neck vs. MRA of peripheral arteries vs. MRA of chest, all under
related CPT codes) or modality role (the same clinical question addressed by
MRI vs. MRA vs. contrast angiography). Do not merge these into one
classification — each region/modality gets its own variant per `SKILL.md`
Step 2, even when they ultimately map to codes in the same family.

### Same code has a repeat-study interval limit

Some codes have conditional frequency limits (e.g., "no more than one [study]
per 90 days absent new symptoms"). Capture the interval and its override
condition (if any) exactly — see `SKILL.md`, "Frequency/interval limits."

### A state redirect and a state statutory override both exist in one document

Some documents combine both patterns at once (e.g., a scope table redirecting
Ohio to a separate policy while an appendix separately overrides Illinois's
reauthorization period and Kentucky's prior-auth duration). Classify and write
each state's situation independently — a redirect for one state says nothing
about whether another state has a statutory override, and vice versa. Do not
resolve multiple state overrides into one compromise rule.

---

## Quick reference: classification summary

| Step | Check                                                              | Result                          |
| ---- | ------------------------------------------------------------------- | -------------------------------- |
| 0    | Which payer, and which source/jurisdiction governs (NCD/LCD+MAC for Medicare; state for Medicaid; plan for MA/Commercial)? Any state redirect or statutory override present? | Determines citation source and scope; state findings become their own segments |
| 1    | Explicitly noncovered or contraindicated?                          | → NONCOVERED (code) or Contraindication Gate (patient-specific) |
| 2    | Named in Coverage Indications with clinical criteria?              | → COPY FROM or NEEDS ORIGINAL   |
| 3    | Has own ICD-10 group assignment?                                   | → COPY FROM or NEEDS ORIGINAL   |
| 4a   | Only exists bundled to a base procedure, no independent indication? | → ADD-ON CODE                   |
| 4b   | Has own indications, but one criterion hinges on another code's outcome? | → OUTCOME-DEPENDENT (adds a Code Dependency; doesn't replace Step 2/3 classification) |
| 5    | Not found anywhere?                                                | → OUT OF SCOPE                  |
