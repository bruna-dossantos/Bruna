# Sen's Questions → Where They're Answered

A direct index against the 10 questions Sen raised, mapped to the exact section(s) of the Criteria Factory Operating Plan. Use this as the cover page if you want to walk him through the doc question-by-question instead of chapter-by-chapter.

---

### 1. What metrics are we tracking from all of this work?

**Answered in:** §5 *Measurement Principles & Metric Layers* (§5.3–§5.6: pipeline productivity, AI output quality, criteria quality dimensions, customer/operational metrics) · §5.2 *Measuring Human Review Impact* · §2.2 *Coverage Readiness Statuses* (readiness, per status) · §7 *How This Becomes a Learning System* (process/infra improvement)

**What it says:** Defines four cross-cutting metric layers plus a dedicated human-review-impact layer, and ties each Coverage Readiness status to what proves it's actually ready — not just "generated."

---

### 2. How do we measure human review impact?

**Answered in:** §5.2 *Measuring Human Review Impact* · §4.3 *Structured Criteria vs. Direct Policy Reasoning* (concrete experimental evidence) · Part II role cards for Criteria Writer and Criteria Reviewer ("Measured by")

**What it says:** Defines defects caught vs. missed, minor-edit-vs-rewrite ratio, an operational definition of "review is still writing, not reviewing," and when review stops earning its cost. The §4.3 experiment supplies the first real data point: faithfulness holds, but a caution flag got dropped mid-process in at least one run — direct evidence human review still catches what automation currently doesn't.

---

### 3. How do we know when it's safe to reduce review? What causes rollback?

**Answered in:** §3 *Review Tier Model* (promotion criteria, rollback triggers) · Review Tier Model diagram (`review_tier_model.svg`)

**What it says:** Eight explicit conditions required before a pattern can move 100% → 30% review, and six triggers that pull any pattern straight back to 100% — tiers move on data, not the calendar.

---

### 4. What experiments will we run to test our assumptions?

**Answered in:** §4 *Experiments: Testing the Model's Assumptions* in full — §4.1 (the standing question bank), §4.2 (Infusions shadow pilot), §4.3 (Structured vs. Direct Policy Reasoning — results in hand), §4.4 (automated building-block generation), §4.5 (patient personas as evaluation context), §4.6 (ticketing adjustments to support all of the above)

**What it says:** A running bank of six standing questions the tier model has to survive, plus five active experiments (one operational pilot, three technical R&D threads, one supporting infrastructure change) each tied to which assumption it tests.

---

### 5. How do we know which work belongs in which review tier?

**Answered in:** §3 *Review Tier Model* ("Applies When" column per tier) · §3.1 *DME: Near-Term vs. Future-State* (why DME and Infusions aren't on the same model)

**What it says:** Tier 1 explicitly triggers on new payer/drug/service line, high-risk logic, shared criteria blocks, and — directly answering the sub-question — **any open customer feedback ticket automatically keeps a pattern at 100% review.** DME and Infusions are called out as needing different timelines because of policy complexity, not preference.

---

### 6. What are we reporting for each work type?

**Answered in:** §5.7 *Reporting by Work Type*

**What it says:** A dedicated report shape for each of eight work types (net-new, AI draft + full review, sampling review, QA audit, customer feedback/custom criteria, payer intelligence, DME service-line packages, POC support) — explicitly rejecting one productivity number for all work.

---

### 7. What is the mapping of the current team to the future functions?

**Answered in:** Part II — every role card's **"Status today"** and **"Should own it"** fields (all 15 roles)

**What it says:** Who's covering each function right now, by name, against who should eventually own it — including where one person is covering multiple functions today (e.g., Bruna and Tess both appear on 5+ role cards).

---

### 8. What is the remaining gap?

**Answered in:** Part II — every role card's **"Gap / risk"** and **"Decision needed"** fields · §11 *Alignment Summary*

**What it says:** Names the actual decision blocking each function — headcount, role clarity, a Mary reset, the Stacey QA-vs-team-lead tradeoff, Payer Intelligence ownership, Product/Eng support, specialty consultants, feedback/custom criteria ownership — rather than a general "we need more people."

---

### 9. How do we measure performance and expectations for each role?

**Answered in:** Part II — every role card's **"Measured by"** field

**What it says:** Role-specific metrics for Writer, Reviewer, QA/Auditor, PjM, Payer Intelligence, Customer Feedback/Custom Criteria Owner, Vertical SME, and Internal Tooling Support — explicitly not one productivity number for all of them.

⚠️ **Open gap, not hidden:** 7 of the 15 roles have no defined metrics yet — Custom Criteria Execution, BI Script Support, Data Labeling/QC Support, Qualifications × Customer Training, Library Management, and a thin version for POC Support. Each is flagged directly on its card rather than papered over. Worth naming to Sen as a known next step, not a blind spot.

---

### 10. How will the data help us monitor and iterate process/infrastructure?

**Answered in:** §7 *How This Becomes a Learning System, Not Just Reporting* (the data source → feeds-back-into table) · §4.6 *Ticketing Method Adjustments* (making sure experiment metadata doesn't disappear)

**What it says:** Names exactly what each data source is supposed to change — wrong-payer flags feed payer mapping fixes, recurring defect patterns feed extraction field/schema redesign, tier-movement recommendations feed the Review Tier Model itself, and §4 experiment results feed pipeline architecture decisions. The loop only works if defect data stays tied to its source, which is why §4.6 exists.

---

## The one gap worth flagging to Sen directly

Question 9 is the only one where the honest answer is "partially" rather than "yes" — 7 of 15 roles still have no defined performance metric. Everything else in his list has a direct, specific answer in the plan.
