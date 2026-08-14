# Medical Qualification Criteria: A Guide to Precision and Reliability

## Introduction: Beyond Copy-Paste

If you're reading this guide, you've been asked to create qualification criteria for medical equipment or services. You might think this means copying requirements from insurance policies into our system. **It doesn't.**

What you're actually doing is more complex and more critical: you're teaching an AI model how to make consistent, accurate decisions about medical eligibility by writing precise instructions that account for the messy reality of healthcare documentation.

This guide focuses on three things that determine whether your criteria will work in production:
1. **What prompt engineering actually means** - Understanding the translation work you're doing
2. **How you format your criteria** - The structure and language that makes criteria work
3. **Why comprehensive testing matters** - Why 5 successful tests doesn't mean you're done

---

## Part 1: Understanding Prompt Engineering

### You're Not Writing Criteria—You're Writing Instructions for an AI

When someone says "write the qualification criteria," they probably imagine you'll:
1. Read an insurance policy
2. Copy the requirements into our system
3. Done

But that's not what's happening. What you're actually doing is **prompt engineering**.

### What Is Prompt Engineering?

Prompt engineering is the practice of designing inputs (prompts) that cause an AI model to produce specific, reliable outputs. It's the difference between:

**Bad prompt:** "Summarize this article"
- Vague, open-ended
- Could be 2 sentences or 10 paragraphs
- Might focus on any aspect of the article
- Different summary every time
- No consistent format

**Good prompt:** "Summarize this article in exactly 3 bullet points, each under 25 words. Focus only on the main findings or conclusions. Do not include background information or methodology. Use present tense."
- Specific output format (3 bullet points)
- Defined length constraint (under 25 words each)
- Clear scope (findings/conclusions only)
- Explicit exclusions (no background, no methodology)
- Style specification (present tense)
- Consistent, predictable results

In the context of qualification criteria, you're doing the same thing. You're taking vague policy language and converting it into prompts that cause the AI model to make specific, consistent qualification decisions.

### The Translation Problem

Here's what makes this challenging: **Insurance policies are written for human auditors who bring contextual understanding, medical knowledge, and judgment to their interpretation.**

An AI model has none of that. It has only what you tell it, exactly as you tell it.

Consider this actual Medicare policy statement:

> "The beneficiary's medical record must contain sufficient documentation of the beneficiary's medical condition to substantiate the necessity for the prescribed item."

A human auditor reads this and understands:
- "Sufficient" means enough detail to justify the decision
- "Medical condition" means diagnosis, symptoms, and functional limitations
- "Substantiate necessity" means prove the patient needs this specific item
- They should look in clinical notes, not the prescription
- Improvement after receiving the item doesn't count as proof of need before receiving it

An AI model reads this and understands:
- Find the words "sufficient documentation"? Or maybe just "documentation"?
- Find "medical condition"—does "patient has pain" count? Does it need a diagnosis code?
- Where should I look? Which document?
- What qualifies as substantiation?

**This is why you're doing prompt engineering.** You must translate the human-readable policy into explicit, unambiguous instructions that an AI model can follow consistently.

### How Prompts Work in Tennr: The Three Components You're Creating

When we talk about "prompt engineering" in the abstract, we're describing the skill you're using. But in Tennr specifically, your prompts create three distinct components that work together:

**1. Extraction Fields** = What Information We Need to Find
- The specific pieces of information that must be pulled from the referral documents to determine if an order qualifies
- These are the data points you're looking for in the paperwork
- **Your extraction prompts create these**
- Examples: patient's diagnosis, date of last doctor visit, specific test results, symptoms described

**2. Criteria** = The Rules for Approval  
- The insurance company's official guidelines/policies translated into executable logic
- These are the "if/then" statements that define medical necessity
- **Your decision logic prompts create these**
- Example: "Patient must have a documented diagnosis of incontinence"

**3. Reasoning** = How the Decision Was Made
- The model's explanation showing its work
- Connects what was found in documents (extraction fields) to whether it met the rules (criteria)
- Results in a qualified or not qualified decision
- **The system generates this automatically by applying your criteria to your extractions**

**Example using all three components:**

| Component | What It Contains |
|-----------|------------------|
| **Extraction field found** | All patient diagnoses (diabetes, hypertension, urinary incontinence) |
| **Criteria required** | One diagnosis must be incontinence |
| **Reasoning** | "Patient has documented diagnosis of urinary incontinence in the medical records. This meets the criteria requirement. Decision: Qualified" |

### The Two Types of Prompts You'll Write

To create these three components, you'll write two distinct types of prompts:

#### Type 1: Criteria Prompts (Decision Logic)

These prompts tell the model: "Given this information, should the patient qualify?"

**Before prompt engineering (policy language):**
> "Patient must have appropriate mobility limitation"

**After prompt engineering (your criteria):**
> "The patient must have a mobility limitation (A, B or C below) that impacts their ability to perform at least one Mobility-Related Activity of Daily Living (MRADL) within the home, in the patient's current unassisted state.
> 
> A. The patient is unable to perform the MRADL without assistance
> 
> OR
> 
> B. Attempting the MRADL without equipment places the patient at increased risk of illness, injury, or medical complications
> 
> OR
> 
> C. The patient cannot complete the MRADL within a reasonable time frame without the prescribed device."

You've translated vague policy language into a specific decision tree the model can follow.

#### Type 2: Extraction Prompts (Search Instructions)

These prompts tell the model: "Find this specific piece of information in the documents."

**Before prompt engineering:**
> "Get the prescription date"

**After prompt engineering:**
> "Extract the date on which the prescription was written, signed, or re-certified. The date may be formatted as MM/DD/YYYY, DD/MM/YYYY, MM/DD/YY, or YYYY-MM-DD. If the recertification date is present and there is not a signature date, use the recertification date. This is usually towards the top of the page or next to the doctor's signature. This cannot come from the fax cover sheet. The signature date should take priority over other dates."

You've anticipated all the variations, specified priorities, identified invalid sources, and told the model exactly where to look.

### Prompt Engineering Is Iterative

Here's the reality: your first version won't work perfectly. That's normal and expected.

Prompt engineering is a cycle:
1. Write initial prompts (your hypothesis)
2. Test against real documents
3. Discover where prompts fail
4. Refine prompts based on failures
5. Test again
6. Repeat until reliable

The testing section of this guide (Part 4) is the second half of the prompt engineering process. You're not just testing criteria—you're discovering where your prompts need refinement and iterating until they work consistently.

### The Goal of Good Prompt Engineering

When you've successfully engineered your prompts, the AI model should:
- Make the same decision a trained human auditor would make
- Make that decision consistently across all documentation variations
- Handle missing information gracefully
- Fail safely (reject when uncertain rather than approve incorrectly)
- Be able to explain its decision based on the criteria you wrote

If the model is making inconsistent decisions, the problem is almost always in the prompt engineering—the criteria aren't explicit enough, don't handle variations, or don't account for real-world documentation patterns.

---

## Part 2: The Two Sides of Tennr (And Why They Must Stay Separate)

The Tennr system has two distinct sides that work together but serve completely different purposes. Understanding this separation is critical to writing criteria that work.

### Left Side: Decision Logic (The Criteria)

**Purpose:** Determines whether a patient qualifies  
**Audience:** Written for clarity and compliance  
**Contains:** The rules, thresholds, and logic for qualification decisions

**Example:**
```
Patient's age must be 3 years or older at the time of prescription
```

This is a decision criterion. It tells the system: "If age is 3+, this criterion passes. If age is less than 3, this criterion fails."

### Right Side: Extraction Instructions (The Search)

**Purpose:** Finds information in documents  
**Audience:** Written to guide data extraction  
**Contains:** Search patterns, location hints, format variations

**Example:**
```
Extract the patient's date of birth or stated age from the prescription or 
medical record. Look for:
- "DOB:" followed by a date
- "Date of birth:" followed by a date  
- "Age:" followed by a number
- Birthdate in patient demographics section
- May be formatted as MM/DD/YYYY, DD/MM/YYYY, or YYYY-MM-DD
```

This is an extraction instruction. It tells the system: "Here's how to find age/DOB information in the documents."

### The Critical Rule: Extractions Must Not Make Decisions

This is where people commonly make mistakes. **Extraction instructions should ONLY find data. They should NEVER evaluate whether that data qualifies.**

**❌ WRONG - Extraction making decisions:**
```
Extract the patient's age from the prescription. The patient must be 3 years 
or older. Look for age or date of birth.
```

**✅ RIGHT - Extraction just finding data:**
```
Extract the patient's date of birth or stated age from the prescription or 
medical record. Look for "DOB:", "Age:", or birthdate in demographics.
```

**Why this matters:**

1. **Separation of Concerns**
   - The LEFT side makes decisions
   - The RIGHT side finds data
   - Mixing them creates confusion and inconsistency

2. **Reusability**
   - A neutral extraction ("find age") can be used by multiple criteria
   - A decision-laden extraction ("find age over 3") only works for that specific criterion

3. **Debugging**
   - If qualification fails, you need to know: Did we find the wrong data? Or did we make the wrong decision?
   - When extractions contain decisions, you can't tell which failed

4. **Transparency**
   - Auditors need to see: What data was found, and how was it evaluated?
   - Mixing extraction and decision makes this unclear

### Real-World Example: The Age Requirement

Let's walk through a complete example to see how the two sides work together.

**Policy Requirement:**
> "Patient must be at least 3 years old"

#### Left Side (Decision Criteria):

```
Patient must be 3 years of age or older at the time of prescription.

If only date of birth is available, calculate age as: 
(Prescription Date - Date of Birth) / 365.25 days

If age is stated without DOB, use the stated age.
```

This is making the decision: what age qualifies, how to calculate it, what to do if only DOB is available.

#### Right Side (Extraction):

```
EXTRACTION FIELD: Patient Age or Date of Birth

Extract patient's age or date of birth from prescription or medical records.

Look for:
- "Age:" followed by a number (e.g., "Age: 5 years", "Age: 3y", "Age 4")
- "DOB:" followed by a date
- "Date of Birth:" followed by a date
- "Born:" followed by a date
- In patient demographics/header section
- Near patient name and address

Format variations:
- Age may be in years, months, or "y/o"
- DOB may be MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, or written out

If both age and DOB present, extract both.
```

Notice what the extraction does NOT say:
- ❌ "Look for age 3 or older"
- ❌ "Patient must be at least 3"
- ❌ "Extract qualifying age"

It just finds the data. The LEFT side decides if that data qualifies.

### How the Two Sides Work Together

Here's the process:

1. **Extraction happens first:**
   - System reads the documents
   - Follows extraction instructions
   - Finds: "Age: 5 years" 
   - Stores: `patient_age = 5`

2. **Decision happens second:**
   - System reads the decision criteria
   - Sees: "Patient must be 3 years of age or older"
   - Compares: `5 >= 3`
   - Result: PASS

3. **System shows both:**
   - To the user: "Patient age is 5 years [extracted from prescription page 1]"
   - Decision: "PASS - Patient is 3 years or older"

This separation means:
- If extraction fails, you know the system couldn't find the data
- If decision fails, you know the data was found but didn't meet criteria
- You can audit each step independently

### More Examples: Decisions vs. Extractions

#### Example 1: Oxygen Saturation

**❌ WRONG - Decision in extraction:**
```
Extract oxygen saturation from sleep study. Must be less than 88% to qualify.
```

**✅ RIGHT - Separated:**

**Left side (Decision):**
```
Patient's oxygen saturation must be less than 88% during ambulation 
or sleep as documented in clinical notes or sleep study.
```

**Right side (Extraction):**
```
Extract oxygen saturation (SpO2) readings from sleep study or medical records.

Look for:
- "SpO2:" followed by a percentage
- "Oxygen saturation:" followed by a percentage
- "O2 sat:" followed by a percentage  
- Values in sleep study results section
- May be labeled as "lowest", "nadir", "average", or "resting"

Extract the value and context (during sleep, during ambulation, at rest).
```

#### Example 2: Prescription Date

**❌ WRONG - Decision in extraction:**
```
Extract prescription date. It must be within 6 months of the face-to-face visit.
```

**✅ RIGHT - Separated:**

**Left side (Decision):**
```
Prescription must be dated no more than 180 days after the face-to-face 
encounter date.
```

**Right side (Extraction):**
```
Extract the date on which the prescription was written, signed, or certified.

Look for:
- "Prescription Date:" followed by date
- "Date:" at top of prescription form
- Date next to prescriber signature
- "Signed on:" followed by date
- May be formatted MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD

If multiple dates present, prioritize signature date over other dates.
Do not use fax date from fax cover sheet.
```

#### Example 3: Face-to-Face Encounter

**❌ WRONG - Decision in extraction:**
```
Extract face-to-face encounter. It must be in person or via telehealth with 
audio and video. Telephone calls don't count.
```

**✅ RIGHT - Separated:**

**Left side (Decision):**
```
A face-to-face encounter must be documented and must be one of the following:
- In-person visit
- Telehealth visit with audio and video
- Televisit with audio and video

The following do NOT qualify:
- Telephone calls (audio only)
- Telehealth/televisit where documentation states no video was used
- Asynchronous communication (portal messages, email)
```

**Right side (Extraction):**
```
Extract information about face-to-face encounters from medical records.

Look for:
- "Face-to-face" / "F2F"
- "In-person" / "office visit" / "clinic visit"
- "Telehealth" / "Televisit" / "Telemedicine"
- "Patient presents for" / "Patient seen for"
- "Examined patient"
- Encounter type in visit note header

Also extract modality if specified:
- "Audio and video"
- "Video visit"
- "Phone call" / "telephone"
- "In person" / "in office"

Extract the encounter date and modality separately.
```

### Why Separation Matters for Testing

When you properly separate decisions from extractions, testing becomes much more effective:

**When extraction and decision are mixed:**
- Failure could be extraction failure OR decision failure—you can't tell
- Can't reuse extraction for other criteria
- Can't test extraction accuracy independently

**When properly separated:**
- You can test: "Did we find the right data?" (extraction test)
- You can test: "Did we make the right decision given that data?" (decision test)  
- You can see: "We found age = 2 years [extraction succeeded] but failed criteria because 2 < 3 [decision worked correctly]"

### Why Separation Matters for Compliance

When auditors review decisions, they need to see:
1. What data was found in the documents
2. What criteria were applied
3. How the criteria evaluated that data

If your extraction says "find age over 3", the auditor can't see what age was actually found. They just see "extraction succeeded" or "extraction failed."

If your extraction says "find patient age" and you find "2 years", the auditor can see:
- ✓ Extraction succeeded: Found "Age: 2 years" on prescription page 1
- ✗ Decision failed: 2 years does not meet requirement of "3 years or older"

This transparency is critical for compliance and appeals.

### Extraction Field Checklist

Before finalizing extraction instructions, verify:

- [ ] Extraction finds data but doesn't evaluate it
- [ ] No threshold values in extraction (those belong in criteria)
- [ ] No qualification logic in extraction (that belongs in criteria)
- [ ] No comparisons in extraction (>, <, ≥, ≤, =)
- [ ] No words like "must", "should", "required" in extraction
- [ ] Extraction would work for any criteria that needs this data
- [ ] You could test extraction accuracy independently of decision logic

---

## Part 3: Writing Effective Criteria

### Why "Just Copy the Policy" Doesn't Work

Let's look at a real example of what happens when you copy policy language directly:

**Medicare LCD says:**
> "Patient is mobile within the home"

You copy this into the system. Now watch what happens with real medical documentation:

**Document 1:** "Patient ambulates throughout home with walker"
- Model decision: PASS (patient is mobile)
- Correct decision: FAIL (patient requires walker—is not independently mobile)

**Document 2:** "Patient is bedbound"
- Model decision: FAIL (patient is not mobile)
- Correct decision: PASS (patient needs equipment because they're not mobile)

The policy language is backwards for how providers document, and it doesn't specify the baseline state. Your prompt engineering fixes this:

**After prompt engineering:**
> "Patient is not bedbound AND patient cannot ambulate safely within the home without assistive equipment in their current unassisted state"

Now the model makes correct decisions on both documents.

### Five Core Principles for Writing Criteria

To write effective criteria, you need to master five core principles:

#### 1. Disambiguation

Taking vague language and making it specific.

**Vague:** "Patient has significant symptoms"

**Disambiguated:** "Patient has at least one of the following symptoms documented in clinical notes: (A) oxygen saturation < 88% during ambulation, (B) shortness of breath limiting daily activities, (C) use of accessory muscles for breathing at rest"

#### 2. Constraint Definition

Specifying exactly what counts and what doesn't count.

**Unconstrained:** "Patient needs wheelchair"

**Constrained:** "Patient needs wheelchair as documented in medical records (not just prescription). Documentation must show patient cannot ambulate safely within home without wheelchair. Comfort, convenience, or preference do not qualify. Improvement with wheelchair does not prove need without wheelchair."

#### 3. Edge Case Handling

Defining what to do when information is missing, ambiguous, or contradictory.

**No edge case handling:** "Face-to-face encounter must be dated"

**With edge case handling:** "Face-to-face encounter must be dated. If multiple encounter dates exist, use the earliest date. If no encounter date exists but visit note is dated, use the note date. If practitioner signature date differs from visit date, use the earlier of the two. If only prescription date exists with notation 'seen today,' the prescription date may serve as encounter date."

#### 4. Explicit Logic Structure

AI models need explicit logical relationships. You must use:

**AND** - All conditions must be met
```
Patient must have Condition A AND Condition B AND Condition C
```

**OR** - Any one condition satisfies the requirement
```
Patient must have Condition A OR Condition B OR Condition C
```

**Complex combinations** - Use parentheses and clear grouping
```
Patient must have (Condition A AND Condition B) OR (Condition C AND Condition D)
```

**❌ Never write:**
- "Patient should meet applicable requirements"
- "Documentation must support medical necessity"
- "Appropriate criteria must be satisfied"

These are meaningless to an AI model. They're like telling someone to "drive appropriately" without defining speed limits, traffic rules, or road signs.

#### 5. Baseline State Specification

Medical documentation is full of statements like:
- "Patient ambulates well with walker"
- "Breathing improved on oxygen"
- "Able to transfer with assistance"

These describe the patient's state WITH intervention, but qualification criteria almost always need to evaluate the patient WITHOUT the device or assistance.

**❌ Ambiguous:**
```
Patient has difficulty walking
```

**✅ Explicit:**
```
Patient has difficulty walking without assistance and without use of 
prescribed equipment, in their current unassisted state
```

**Why this matters:** Without the baseline state specified, the model might read "patient walks well with a walker" and incorrectly conclude the patient can walk, disqualifying them from equipment they need.

This phrase should appear repeatedly in your criteria:
- "without assistance"
- "without the device"
- "in the patient's current unassisted state"
- "prior to receiving the prescribed equipment"

It feels redundant. That's the point. Redundancy creates guardrails.

### Handling Variation in Medical Documentation

Providers don't use standardized language. The same concept appears in dozens of ways:

**Concept:** Face-to-face encounter

**Real-world variations:**
- "F2F visit"
- "Seen in office"
- "Patient presents for evaluation"
- "Telehealth encounter"
- "Virtual visit"
- "In-person assessment"
- "Televisit"
- "Examined patient today"

Your criteria must account for this. Not by listing every variation in the criterion itself, but by handling it in your extraction instructions.

**In the criterion (left side):**
```
Face-to-face encounter must be documented
```

**In the extraction (right side):**
```
A face-to-face encounter can be indicated by:
- "face-to-face" / "F2F"
- "telehealth" / "televisit" / "telemedicine"
- "patient presents" / "patient seen"
- "in-person" / "office visit"
- "examination" with a date
- Or any phrasing that implies a clinical encounter occurred
```

### Common Formatting Failures

Here are the most common ways criteria fail due to formatting issues:

| Problem | Why It Fails | Fix |
|---------|--------------|-----|
| **Vague quantifiers** | "Patient has significant difficulty breathing" - What's significant? | "Patient's oxygen saturation falls below 88% during ambulation" |
| **Undefined timeframes** | "Recent face-to-face visit" - How recent? | "Face-to-face encounter within 12 months prior to prescription date" |
| **Assumed context** | "Patient uses device regularly" - How often is regular? | "Patient uses device at least 5 days per week as documented in medical records" |
| **Circular logic** | "Patient qualifies if they meet medical necessity" - What is medical necessity? | Define the specific clinical criteria that constitute medical necessity |
| **Missing document location** | "Patient has diagnosis of COPD" | "Patient has diagnosis of COPD documented in the medical record problem list, assessment, or diagnosis section" |

### The Criteria Formatting Checklist

Before moving to testing, verify every criterion meets these standards:

**Logic Structure:**
- [ ] Every AND/OR relationship is explicit
- [ ] Complex logic uses clear grouping with parentheses or sublists
- [ ] No phrases like "appropriate," "applicable," or "as needed" without definition

**Baseline State:**
- [ ] Criteria specify "without assistance" where relevant
- [ ] Criteria specify "without the device" where relevant
- [ ] The evaluation context is clear (pre-treatment vs. post-treatment)

**Precision:**
- [ ] Timeframes use specific durations (days, weeks, months)
- [ ] Quantities use specific numbers or ranges
- [ ] Qualitative terms are defined or avoided
- [ ] Document locations are specified (which section, which document type)

**Variation Handling:**
- [ ] Extraction instructions include common synonyms
- [ ] Extraction instructions include common abbreviations
- [ ] Extraction instructions handle formatting variations (dates, names, etc.)

---

## Part 4: Testing Your Criteria

### Why "It Worked 5 Times" Doesn't Matter

You've written your criteria. You've tested them on 5 packets. All 5 passed correctly. You think you're done.

**You're not even close.**

Here's what you've actually proven: your criteria work on 5 specific examples. Here's what you haven't proven:

- They work on documents from different providers
- They work when information is formatted differently
- They work when information is in unexpected locations
- They work when information is partially missing
- They work when wording is ambiguous
- They work on edge cases near the qualification threshold
- They handle negative cases correctly (properly rejecting unqualified patients)
- They're consistent across similar scenarios

### The Statistical Reality

Let's say your criteria will eventually process 1,000 real patient packets. If you test 5 packets:

- You've evaluated 0.5% of your sample size
- You've likely seen only the most common, straightforward cases
- You haven't encountered the long tail of edge cases
- Your confidence interval is essentially meaningless

Now let's say you test 30 packets:

- You've evaluated 3% of eventual volume
- You've started to see variation in documentation
- You can identify patterns in how criteria perform
- You can calculate meaningful error rates
- You can start to trust your criteria

**This is why we require 30+ test cases.** Not because we picked a random number, but because it's the minimum needed to see real variability in healthcare documentation.

### What Comprehensive Testing Reveals

#### Discovery 1: Provider Variation

Your first 5 tests might come from Provider A, who:
- Always includes clear diagnostic codes
- Always signs and dates documents in the same location
- Uses standardized templates
- Never abbreviates

Then test 6 comes from Provider B, who:
- Uses local diagnostic terminology
- Signs documents in random locations
- Has handwritten notes
- Abbreviates everything

Your criteria that worked perfectly on Provider A's documents now fail on Provider B's. You haven't changed anything about the clinical requirements - you've just encountered real-world variation.

**This is normal and expected.** The testing process is how you discover this variation and make your criteria robust enough to handle it.

#### Discovery 2: Edge Cases Near Thresholds

Your criteria might say: "AHI must be ≥ 15 events per hour"

Your first 5 tests might have AHI values of:
- 42 (pass - clear)
- 8 (fail - clear)
- 51 (pass - clear)
- 12 (fail - clear)
- 38 (pass - clear)

Great! Your criteria work!

But then tests 6-30 include:
- 14.9 (should fail, but documentation says "approximately 15" - how do you handle that?)
- 15.0 (should pass, but it's documented as "AHI: 14-16 range" - do you take the lower bound?)
- 15.2 (should pass, but there's a note saying "may be inflated due to poor sleep quality" - do you count it?)

These threshold cases reveal whether your criteria make consistent decisions when evidence is ambiguous. Five tests won't find these - 30 tests will.

#### Discovery 3: Missing Information Patterns

Your criteria might require: "Face-to-face encounter within 12 months of prescription"

Your first 5 tests might all have clear, dated encounter notes. Perfect!

But tests 6-30 reveal:
- 3 packets with no encounter date (only a prescription date)
- 2 packets with multiple encounter dates (which one counts?)
- 4 packets where the encounter note is unsigned
- 2 packets where the encounter was by phone (does that count as face-to-face?)
- 1 packet where the encounter is documented but falls on the prescription date (is it before or after the prescription?)

Now you realize your criteria need fallback logic:
- What if the encounter date is missing but the prescription date is present?
- What if multiple encounters exist - do you take the earliest, latest, or closest to prescription?
- What if the encounter type is ambiguous?

Without testing 30+ packets, you won't discover these scenarios. You'll deploy criteria that work in ideal conditions and fail in real-world messiness.

#### Discovery 4: False Positives vs. False Negatives

There are two ways criteria can fail:

**False Negative:** Rejecting a patient who should qualify
- Annoying for the patient and provider
- Creates rework
- Costs time and money
- Damages customer satisfaction

**False Positive:** Approving a patient who shouldn't qualify
- Creates compliance risk
- Can trigger audits
- Can result in denied claims
- Can result in financial penalties
- Damages your credibility

False positives are more dangerous. You need enough tests to catch them.

With 5 tests, you might see:
- 4 clear passes
- 1 clear fail

With 30 tests, you see:
- 18 clear passes
- 8 clear fails
- 3 borderline passes (need to verify they're correct)
- 1 false positive (criteria passed but shouldn't have)

That one false positive is gold. It reveals a flaw in your logic that could have caused major problems in production.

### The Testing Protocol

#### Phase 1: Initial Testing (5 Packets)

**Purpose:** Catch catastrophic failures early

**What you're looking for:**
- Does the model extract any data at all?
- Are document types being identified correctly?
- Is the basic logic working as intended?
- Are there obvious formatting problems?

**Expected outcome:** You should find problems. If you don't, your test set might not be diverse enough.

**What to do:**
- Fix major issues
- Refine prompt language
- Adjust document type identification
- Don't proceed until these 5 work consistently

#### Phase 2: Bulk Testing (30+ Packets)

**Purpose:** Validate reliability across variation

**What you're looking for:**
- Patterns in failures (e.g., always fails when signature is in header)
- Provider-specific issues (e.g., works for Provider A but not Provider B)
- Edge cases near thresholds
- Handling of missing or ambiguous information
- False positives (passing when should fail)
- Consistency across similar scenarios

**Test composition should include:**
- 15-20 clear passes (obviously qualified)
- 5-8 clear fails (obviously not qualified)
- 5-7 edge cases (near thresholds, ambiguous documentation)
- Mix of providers/documentation styles
- Mix of complete and incomplete documentation
- At least 2-3 cases from each major document format variation

**Expected outcome:** You may find problems in 20-40% of cases on first run. This is normal.

**What to do:**
- Document every failure with specific reason
- Categorize failures:
  - Extraction failure (didn't find the data)
  - Logic failure (found data but applied wrong logic)
  - Threshold failure (borderline case handled wrong)
  - Document type failure (looked in wrong document)
- Refine criteria based on patterns
- Retest ALL 30 after changes (don't just retest the failures)

#### Phase 3: Iteration

**Purpose:** Achieve reliability threshold

**Process:**
1. Review all failures from Phase 2
2. Identify root causes (extraction? logic? ambiguity?)
3. Refine criteria to address root causes
4. Retest all 30 packets
5. Track improvement: First run might be 60% accuracy → Second run might be 85% → Third run might be 95%
6. Continue until you hit 95%+ agreement with ground truth

**Critical rule:** When you change criteria, you must retest everything, not just the failures.

Why? Because fixing one problem can create new problems elsewhere. The only way to know is comprehensive retesting.

### The Testing Mindset

Effective testing requires a specific mindset:

**❌ Wrong mindset:**
- "I want my criteria to pass all tests"
- "If it passes 5 tests, it's done"
- "Failures mean I did something wrong"

**✅ Right mindset:**
- "I want to find every way these criteria can fail"
- "Failures are valuable data that make my criteria better"
- "Comprehensive testing is how I build reliability"
- "30 tests is the minimum, not the target"

Think of yourself as trying to break your own criteria. Every failure you find in testing is a failure you prevented in production.

### Metrics That Matter

Track these metrics during testing:

**Agreement Rate:**
(# of correct decisions / total tests) × 100

Target: 95%+ before considering criteria complete

**False Positive Rate:**
(# of incorrect approvals / total should-fail cases) × 100

Target: 0% (these are most dangerous)

**False Negative Rate:**
(# of incorrect rejections / total should-pass cases) × 100

Target: <5% (these are annoying but less dangerous)

**Extraction Accuracy:**
(# of correctly extracted fields / total fields) × 100

Target: 98%+ (even if logic is perfect, bad extractions cause failures)

### When Are You Actually Done?

You're done when:
- [ ] You've tested at least 30 diverse packets
- [ ] Agreement rate is 95%+
- [ ] False positive rate is 0%
- [ ] You've tested multiple provider documentation styles
- [ ] You've tested edge cases near qualification thresholds
- [ ] You've tested cases with missing information
- [ ] You've documented all remaining edge cases that can't be resolved
- [ ] You've retested after every criteria change
- [ ] You've had at least one complete test run with zero changes needed

If you haven't checked all these boxes, you're not done, regardless of how good your numbers look.

---

## Part 5: Common Mistakes and How to Avoid Them

### Prompt Engineering Mistakes

#### Mistake: Using Policy Language Verbatim

**Why it fails:** Policy language is written for humans with medical knowledge and contextual understanding, not AI models.

**Example:**
- Policy: "Patient must have appropriate mobility limitation"
- Problem: What is "appropriate"? How do you measure a limitation?

**How to avoid:** Translate every policy statement into explicit, testable criteria:
- "Patient must have a mobility limitation that prevents them from performing at least one MRADL without assistance, places them at increased risk of injury when attempting the MRADL, or prevents completion of the MRADL within a reasonable timeframe"

#### Mistake: Assuming Shared Knowledge

**Why it fails:** The model doesn't know medical terminology, clinical context, or common practices.

**Example:**
- Criterion: "Patient needs CPAP"
- Problem: Model doesn't know what symptoms indicate CPAP need

**How to avoid:** Define everything explicitly:
- "Patient must have sleep apnea diagnosed via sleep study showing AHI ≥ 5 events per hour AND one of: excessive daytime sleepiness, hypertension, or history of stroke"

#### Mistake: One-Shot Prompting

**Why it fails:** Your first attempt will almost never capture all edge cases and variations.

**Example:**
- Writing criteria once and immediately deploying to production

**How to avoid:** Plan for iteration:
- Test with 5 packets → revise
- Test with 30 packets → revise
- Test again → verify
- Only then deploy

#### Mistake: Ignoring the Negative Case

**Why it fails:** Only defining what qualifies means you don't catch false positives.

**Example:**
- Criterion: "Patient has diagnosis of incontinence"
- Problem: What if diagnosis is "resolved incontinence"?

**How to avoid:** Explicitly define what disqualifies:
- "Patient has diagnosis of urinary incontinence OR urinary retention. The following do NOT qualify: resolved incontinence, temporary incontinence due to acute illness, incontinence managed without catheterization"

#### Mistake: Missing Fallback Logic

**Why it fails:** Real documentation is messy—information is often missing or ambiguous.

**Example:**
- Criterion: "Prescription date must be within 180 days of face-to-face encounter"
- Problem: What if there's no encounter date, only a prescription date?

**How to avoid:** Define what to do when data is missing:
- "If encounter date is not documented but prescription includes notation 'seen today' or 'patient in office,' prescription date may serve as encounter date"

### Formatting Mistakes

#### Mistake: Including Thresholds in Extractions

**Why it fails:** Mixes data finding with decision making, makes debugging impossible.

**Example:**
- Extraction: "Extract AHI if ≥ 15"

**How to avoid:** 
- Extraction: "Extract AHI value from sleep study"
- Criteria: "AHI must be ≥ 15 events per hour"

#### Mistake: Including Qualification Logic in Extractions

**Why it fails:** Can't reuse extraction, can't test independently, unclear audit trail.

**Example:**
- Extraction: "Find face-to-face visit within 6 months"

**How to avoid:**
- Extraction: "Find face-to-face visit date"
- Criteria: "Face-to-face visit must be within 180 days of prescription"

#### Mistake: Making Comparisons in Extractions

**Why it fails:** Extraction should find numbers, criteria should compare them.

**Example:**
- Extraction: "Find blood pressure over 140/90"

**How to avoid:**
- Extraction: "Find systolic and diastolic blood pressure readings"
- Criteria: "Systolic BP ≥ 140 mmHg OR diastolic BP ≥ 90 mmHg"

#### Mistake: Including Exclusions in Extractions

**Why it fails:** Extraction should find all relevant data; criteria should filter it.

**Example:**
- Extraction: "Get diagnosis but not if it's for comfort only"

**How to avoid:**
- Extraction: "Extract all documented diagnoses and their context"
- Criteria: "Diagnosis must indicate medical necessity. Diagnoses documented as 'for comfort only' or 'convenience' do not qualify"

#### Mistake: Combining Multiple Fields in One Extraction

**Why it fails:** Makes it impossible to tell which piece of data is missing if extraction fails.

**Example:**
- Extraction: "Get age and verify over 3"

**How to avoid:** Create separate extractions:
- Extraction 1: "Extract patient age or date of birth"
- Extraction 2: "Extract prescription date"
- Criteria: "Patient must be 3 years or older at prescription date"

### Testing Mistakes

#### Mistake: Testing Only "Happy Path" Cases

**Why it fails:** Real world includes incomplete documentation, edge cases, and documents that should fail.

**Example:**
- All 30 test packets are perfect examples with complete documentation

**How to avoid:** Intentionally include:
- Packets missing critical information
- Packets with ambiguous wording
- Packets near qualification thresholds
- Packets that should clearly fail
- Packets from multiple providers with different documentation styles

#### Mistake: Changing Criteria Without Full Retesting

**Why it fails:** Fixing one criterion can break another; you won't know without complete retesting.

**Example:**
- Fix extraction for prescription date → retest only packets that failed on prescription date

**How to avoid:** After ANY change:
- Retest all 30 packets
- Track new failure patterns
- Verify the fix didn't create new problems

#### Mistake: Not Documenting Edge Case Decisions

**Why it fails:** Creates inconsistency when similar cases appear later; no institutional memory.

**Example:**
- Encounter AHI value of "14-16 range," decide to use 14, don't document why

**How to avoid:** Document:
- What was ambiguous
- What decision you made
- Why you made it
- Alternative interpretations considered

#### Mistake: Ignoring Patterns in Failures

**Why it fails:** Treating symptoms instead of root causes means failures will recur.

**Example:**
- 5 failures all involve handwritten signatures → fix each individually

**How to avoid:** Categorize failures:
- All 5 are extraction failures for signature detection
- Root cause: Extraction prompt doesn't handle handwritten signatures
- Fix: Update extraction to look for handwritten signatures in signature area
- Result: Fixes all 5 at once

#### Mistake: Stopping at 95% Accuracy

**Why it fails:** The remaining 5% might all be dangerous false positives or clustered errors.

**Example:**
- Hit 95% accuracy, declare victory, don't analyze the 5% errors

**How to avoid:** Analyze the errors:
- If 5% is random noise across all categories → probably done
- If 5% is all false positives → critical problem, must fix
- If 5% is all from one provider → need better variation handling
- If 5% is all one edge case → need to define that edge case

---

## Part 6: The Refinement Loop

Good criteria emerge through iteration. Here's the cycle:

### 1. Write Initial Criteria

Based on policy documents and your understanding of requirements. This is your hypothesis about what will work.

**Time investment:** 2-4 hours for complex criteria

### 2. Initial Test (5 packets)

Find obvious problems quickly.

**Time investment:** 1-2 hours including fixes

### 3. Bulk Test (30 packets)

Find subtle problems and patterns.

**Time investment:** 3-4 hours for first run

### 4. Analyze Failures

Categorize, find patterns, identify root causes.

**Time investment:** 1-2 hours

### 5. Refine Criteria

Make targeted improvements based on failure analysis.

**Time investment:** 1-2 hours

### 6. Retest Everything

Verify improvements without creating new problems.

**Time investment:** 2-3 hours

### 7. Repeat Steps 4-6

Until you hit reliability threshold.

**Time investment:** 2-3 iterations typical (6-9 hours)

### Total Time Investment

Expect 15-25 hours from initial draft to production-ready criteria for complex products. This is normal and necessary.

If someone tells you they completed criteria in 3 hours, one of three things is true:
1. The criteria are very simple (RX only, no clinical requirements)
2. They're using existing criteria as a template (minimal new work)
3. They didn't test comprehensively (and the criteria will fail in production)

---

## Part 7: Quick Reference Guide

### Criteria Formatting Checklist

**Before testing, verify:**
- [ ] All AND/OR logic is explicit
- [ ] "Without assistance" appears where needed
- [ ] "Without the device" appears where needed
- [ ] Timeframes use specific numbers (not "recent")
- [ ] Quantities use specific numbers (not "frequent")
- [ ] Document locations are specified
- [ ] Extraction prompts include common variations
- [ ] No undefined terms like "appropriate" or "applicable"
- [ ] Baseline state is clear throughout

### Extraction Field Checklist

**Before finalizing extractions:**
- [ ] Extraction finds data but doesn't evaluate it
- [ ] No threshold values in extraction (those belong in criteria)
- [ ] No qualification logic in extraction (that belongs in criteria)
- [ ] No comparisons in extraction (>, <, ≥, ≤, =)
- [ ] No words like "must", "should", "required" in extraction
- [ ] Extraction would work for any criteria that needs this data
- [ ] You could test extraction accuracy independently of decision logic

### Testing Checklist

**Before declaring criteria complete:**
- [ ] Tested at least 30 diverse packets
- [ ] Agreement rate ≥ 95%
- [ ] False positive rate = 0%
- [ ] False negative rate < 5%
- [ ] Tested multiple provider styles
- [ ] Tested edge cases near thresholds
- [ ] Tested cases with missing information
- [ ] Tested cases that should fail
- [ ] Retested after every criteria change
- [ ] Documented all edge case decisions
- [ ] Analyzed failure patterns, not just individual failures

### Red Flags That Indicate More Work Needed

🚩 All test cases pass on first try (test set not diverse enough)  
🚩 Only testing obvious passes (need more fails and edge cases)  
🚩 False positive rate > 0% (dangerous - must fix)  
🚩 All failures are from one provider (need more provider diversity)  
🚩 Can't explain why a decision was made (logic is unclear)  
🚩 Making criteria changes without full retesting  
🚩 Unable to categorize failures into patterns  
🚩 Test documentation is incomplete  

---

## Conclusion: Precision Enables Scale

You might wonder why we're so demanding about formatting and testing. After all, humans have been making these qualification decisions for years without all this structure.

The answer is scale and consistency.

A human reviewer can look at ambiguous documentation and make a reasonable judgment call. But that judgment call will vary:
- Between reviewers
- For the same reviewer on different days
- Based on context and experience
- Based on how the question is framed

When you write criteria for an AI model, you're creating a decision-making system that will:
- Process thousands of cases
- Make the same decision every time for the same inputs
- Work 24/7 without fatigue
- Scale infinitely without adding headcount

But to achieve this, the system needs precision that human workflows don't require. Every ambiguity, every undefined term, every missing variation gets multiplied across thousands of cases.

That's why formatting matters. That's why comprehensive testing matters. You're not just writing criteria for one case - you're building a reliable decision-making system that will handle every variation, every edge case, every imperfection in real-world healthcare documentation.

When you invest the time to format criteria precisely and test them comprehensively, you create something that works reliably at scale. When you cut corners, you create something that seems to work in testing but fails in production.

The choice is yours. We recommend precision.
