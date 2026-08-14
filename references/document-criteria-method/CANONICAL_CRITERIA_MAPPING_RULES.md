# Canonical Criteria Mapping — How to Read and Evaluate a Requirement

How to decide which canonical criteria a source requirement maps to. Derived from
the J&B prescription-requirement build (Jul 2026) and Bruna's corrections during it.
Every rule below exists because getting it wrong produced a real defect.

Companion documents:
- `JB_SPECIFIC_RULES.md` — J&B-specific classifications and payer conventions
- `MAPPING_VALIDATION_RULES.md` — how to verify work against both documents

---

## 0. The core principle

**Map the requirement to what it actually asks the model to find — not to the word it
resembles.** Two requirements that share a word are often different fields, and one
requirement often names two fields.

The three failure modes, in order of how often they occurred:

| Failure | Example | Rule violated |
|---|---|---|
| Over-merging distinct fields | `Oxygen Liter Flow` + `PO2 Value` + `Test Results` all collapsed into one "PAP and Sleep Study" concept | §2 |
| Losing a constraint | `Diagnosis (E10-E13.9 only)` mapped to generic `Diagnosis`, dropping the code list | §5 |
| Silently dropping half a requirement | `Quantity and Frequency` mapped only to Quantity | §6 |

---

## 1. Read the section context before the text

The same words mean different fields depending on which section of the source
document they appear in.

| Text | In Member section | In Physician section |
|---|---|---|
| `Name` | Patient Name | Prescriber Name |
| `Address` | Patient Address | Prescriber Address |
| `Address & Phone` | Patient Address + Phone | Prescriber Address + Phone |

**But an explicit qualifier overrides the section.** `Member Full Name` inside the
Physician section is still Patient Name. Qualifier beats position.

Sections that are *whole-prescription* (they belong to the base document, not a
product): Member/Patient, Physician/Prescriber, Signature, Diagnosis Requirements.

---

## 2. One field per criteria — never merge distinct fields

Merge **only** genuine synonyms of the same field. If two requirements could be
satisfied by different values on the page, they are different criteria.

**Merge** — same field, different wording:
```
Patient's Name · Patient Name · Member's Name · Individual Name · Recipient Name
      → Patient Name
```

**Do NOT merge** — related topic, different field:
```
Oxygen Liter Flow · Oxygen Saturation Level · PO2 Value      (3 criteria)
Test Date · Test Method · Test Results                        (3 criteria)
PAP Pressure Settings · CPAP Supplies · Apnea/Hypopnea Index  (3 criteria)
Enteral Formula Name · Caloric Density · Total Calories per Day · Volume per Feeding
```

Product families are **not** concepts. "Wound Care" is a section; `Wound - Location`,
`Wound - Size`, `Wound - Drainage`, `Wound - Thickness` are four criteria.

### The timeframe/type IS the requirement

Never merge across a differing threshold — the number is the rule:
```
Rx Recency - 1 Year · - 90 Days · - 60 Days · - 30 Days
Chart Notes Recency - 1 Year  vs  - 6 Months
Encounter Recency - 1 Year    vs  - 6 Months
```
Derive the timeframe from the **definition text**, not the label. `Encounter Recency`
appears with both 6-month and 12-month definitions under the same label — they are
two criteria.

### Distinguish by identifier type and role

```
Patient Medicaid ID   ≠  Patient Insurance ID        (Medicaid ≠ commercial)
Prescriber NPI  ≠  Prescriber License Number  ≠  Prescriber Texas Provider ID
Diagnosis  ≠  Diagnosis Code/ICD-10  ≠  Primary  ≠  Secondary  ≠  Supporting
Evaluator / Prescriber / Supplier / DMEPOS Provider are four different people
```

---

## 3. Prefer the house-format definition

When several definitions describe the same concept, the canonical is the one written
in house format — **not** the one whose source document happens to be generic.

House format is recognisable by:
- "The document must include / identify …"
- "Acceptable diagnoses may include, but are not limited to …"
- "Review the entire document and return every qualifying diagnosis found."
- "Do not stop after identifying the first qualifying diagnosis."
- "If … this requirement is not met."

A terse extraction one-liner (`Locate the ICD 10 code or the narrative description`)
must never outrank a full house-format definition. This was a real defect: the
house-format `Diagnosis - Underlying Cause` was losing to the generic `Causative DX`
blurb purely on source.

### Never use ordinal words the model will hunt for

> "Cannot use the words secondary or primary — it tries to actually find that."

The model searches for a field literally labelled "Secondary Diagnosis". Express the
concept by **role**, not position. The house word for the additional diagnosis is
**"supporting diagnosis"**.

```
✗ "the secondary diagnosis"        → model looks for a Secondary Diagnosis field
✓ "a supporting diagnosis"         → model understands the concept
✓ "beyond the first qualifying diagnosis found"
```

---

## 4. Canonical selection order

When one concept has several candidate rows, pick in this order:

1. **Canonical Library** (`document_name = "Canonical Library"`) — authored as the
   standard, wins outright.
2. **Universal + house-format** — portable wording, reusable on any document.
3. **Universal** — portable wording (generic → payer-sourced → customer-sourced).
4. **Form-Level** — wording anchored to one form's layout.

Within a tier: house-format first, then most recent, then longest definition.

### Form-bound is not a defect

A definition that says `Look in Section A under the Customer column` cannot be
canonical *universally* — but it **is** canonical for its **form class**, reusable
when building another form of that kind (another CMN, another wheelchair eval).

Form-bound markers: names a form section/part/box/line · points at a labeled field ·
quoted form field · named column · "value next to the term" · checkbox/bubble
selection · "bottom of the form".

**Not** form-bound — soft positional hints are fine:
```
✓ "typically found towards the bottom of the document"
✓ "may be labeled as 'Duration of Need', 'Length of Need', or 'Rental Period'"
    ← guidance about alternative NAMES, valid on any document
✗ "the field labeled 'Medicaid ID number'"
    ← points at one form's layout
```

---

## 5. Preserve payer-specific constraints as their own criteria

A code list or exclusion is **not** satisfied by the generic concept. Capture it.

| Constraint type | Naming | Behaviour |
|---|---|---|
| Required code list | `Diagnosis Codes - <Product> - <ranges>` | at least one listed code must be present |
| Excluded codes | `Diagnosis Codes - <Product> - Excluded DX (<codes>)` | a listed code disqualifies |
| Conditional rule | `Diagnosis Codes - <Product> - <rule> (<codes>)` | compound logic |

**Naming convention:** `Diagnosis Codes - Product - DX Range / Code` or
`Diagnosis Codes - Product - Excluded DX`. Product comes from the section the
requirement appeared in; fall back to inferring from the code family
(E08–E13 → Diabetic, R32/N39/F98 → Incontinence, Z39 → Breast Pump).

Keep near-identical lists **separate**. `E08-E13.9` and `E10-E13.9` differ by one
code; merging silently loosens the constraint for the narrower payer.

### Required vs excluded wording

Allowlist — extra diagnoses do **not** fail the order:
> …at least one diagnosis the payer accepts… **However, the presence of additional
> diagnoses outside the accepted ranges does not cause the requirement to fail when
> at least one accepted diagnosis is also documented.**

Single excluded code — disqualifying on sight:
> If R32 is documented anywhere on the document, this requirement is not met,
> **regardless of whether other diagnoses are also documented.**

---

## 6. A compound requirement produces every criteria it names

> "If the source asks for both quantity and frequency, break that into 2 requirements
> and map it to each."

| Source text | Criteria produced |
|---|---|
| `Quantity and Frequency` | Quantity Ordered **+** Frequency of Use - Days |
| `Address & Phone Number` | Prescriber Address **+** Prescriber Phone Number |
| `Duration/Refills - max 12 months` | Length of Need - 12 Month Max (Accepts 99) **+** Number of Refills |
| `Fax and Phone Number` | Prescriber Fax Number **+** Prescriber Phone Number |
| `…signature and date of signature` | Prescriber Signature **+** Prescriber Signature Date |
| `License, Texas Provider ID and NPI` | License **+** NPI **+** Texas Provider ID |

**The specific label stays primary; the compound only adds.** `Duration/Refills - max
12 months` keeps `Length of Need - 12 Month Max (Accepts 99)` as its primary and adds
`Number of Refills` — it must not fall back to generic `Length of Need`.

Do **not** create a bundled multi-field criteria. Emit each separately and combine at
the order-type level.

---

## 7. A negative rule still asserts the requirement

> "If 'Electronic and stamped signatures are NOT accepted' assume that it is still
> needed."

A restriction on *how* a field may be satisfied still requires the field.

```
"Electronic and stamped signatures are NOT accepted"  → Prescriber Signature
"PRN or as needed are not acceptable"                 → PRN / As Needed - Not Acceptable
"Stress/Urge/Overflow incontinence are not acceptable diagnoses"
        → EXCLUSION on Diagnosis - Type of Incontinence
```

Diagnosis exclusions are **not** new criteria — they are constraints belonging inside
an existing criteria's acceptable/unacceptable list. Status `EXCLUSION`.

---

## 8. Exclude what is not a prescription requirement

Content living under the Prescription Requirements heading that is **not** a field to
extract from the order:

| Status | What it covers |
|---|---|
| `NOT RX — PA / Coverage` | prior-auth triggers, precertification |
| `NOT RX — Coverage Limit` | quantity limits, MUEs, "not a covered benefit" |
| `NOT RX — Age Restriction` | age-based coverage rules |
| `NOT RX — Ops / Workflow` | HDMS/OnBase steps, "call the physician office", "see a supervisor" |
| `POLICY` | order-confirmation workflow, colour-coding legends, ship cadence |
| `REFERENCE` | `[Rx] Template` names, cross-references, DAW allowances |

**Guard:** a line that names a required field is criteria even if it also mentions a
consequence.
```
✗ discard: "Prior authorization is always required for code T4543…"
✓ keep:    "Secondary diagnosis - type of incontinence, MUST be one of the
            following otherwise a PA is required"   ← states a field requirement
```

Exclude these from coverage percentages — they aren't requirements, so counting them
understates coverage.

---

## 9. Status vocabulary

| Status | Meaning |
|---|---|
| `EXISTS` | a canonical criteria covers it as-is |
| `BUILT` | covered by a criteria created in the Canonical Library |
| `EXISTS-JB` | covered by a J&B-specific criteria |
| `PARTIAL` | nearest criteria exists but wording/scope must be extended |
| `EXCLUSION` | payer constraint to encode inside an existing criteria |
| `MEDICARE-SWO` | requirement is "follow Medicare guidelines" → inherits the SWO |
| `GAP` | no criteria exists — must be authored |
| `UNMAPPED` | nothing matched; needs review |
| `NOT RX — *` / `POLICY` / `REFERENCE` | not a prescription requirement |

`GAP` must reach **zero** before a build is complete. `UNMAPPED` is the honest
residual — never map something loosely just to clear it.

---

## 10. Reading the source document correctly

Mapping is only as good as extraction. These caused silent data loss:

**A section header is an `<h1>`–`<h4>`, or an `<li>` whose children hang off the next
`<ul>`, or ALL-CAPS text, or text ending in a colon.** A plain title-case `<li>` among
siblings is a **value**. `Diabetes` inside an approved-diagnosis list is a value; when
treated as a header it opened a bogus "Diabetic Testing" section and swallowed the
rest of the list.

**Normalise the source before matching.** The wiki contains zero-width spaces inside
words, hard wraps mid-value, and misspellings:
```
Prescription Requirements · Prescription/CMN Requirements
Prescripti​​on Requirements (zero-width spaces) · Prescription Reqiurements
Prescritpion Requirements · BCN Prescription Requirements
Provider Type: → "OUT OF" / "NETWORK"   (value wrapped across two lines)
Physician O rder form · instru ctions   (space inside a word)
```

**Codes written without decimals** (`E8881` → `E88.81`) must be normalised — but
**only on diagnosis lines**. HCPCS supply codes have the identical shape, and
normalising them invents diagnoses: `A4927` (gloves) → "A49.27", `T4543` (bariatric
brief) → "T45.43".

**Strip navigation chrome** before treating content as requirements.

---

## 11. Every mapping must be auditable

Carry through, on every row:
- the **verbatim** source text
- the section it came from
- a link to the cached page and the live wiki URL

If a mapping can't be traced back to its source line, it can't be confirmed.
