# Criteria Factory Operating Plan
### Readiness, Review Model, Measurement, Feedback, and Resourcing

**Owner:** Bruna Dos Santos | **Status:** Draft for review | **Last updated:** June 30, 2026

---

# Part I — The Case

## Executive Summary

**Thesis:** The Criteria Factory model is the right destination, but the team cannot safely scale until the operating model, measurement layer, review gates, tooling dependencies, and ownership gaps are made explicit.

This is not a request to slow down — it's a plan to make the work scalable **in the correct order**.

The organization is still treating the gap as a writer-productivity or reviewer-training issue. Those matter, but they aren't the main blockers. The real blockers are structural:

- Pipeline output is not consistently reviewable
- Eval testing is still manual
- There's no reliable bulk packet-testing path
- Payer mapping and policy source validation aren't cleanly owned
- Customer feedback, custom criteria work, and POC support are consuming unplanned capacity
- Specialty verticals are expanding faster than SME coverage
- Current reporting captures activity — not readiness, quality, rework, customer impact, or sustainability

> **The factory is working only when throughput increases without increasing rework, defects, customer feedback, SLA misses, or after-hours effort.**

**What needs to change first:**

1. Define **Coverage Readiness** so "generated," "reviewed," "tested," and "live" stop being treated as the same thing.
2. Separate net-new criteria production from customer feedback and custom criteria execution.
3. Move DME from isolated ticket work to **payer + plan category + service-line package** tracking after Comfort.
4. Pilot reviewer-mode in Infusions through a **shadow experiment** before reducing review operationally.
5. Build explicit ownership for QA, Payer Intelligence, Customer Feedback / Custom Criteria, PjM control, and specialty support.
6. Prioritize Product/Engineering dependencies that make the factory measurable — especially **bulk packet testing**.

---

## 1. Why Criteria Factory Needs an Operating Model

### 1.1 The destination is right; the gap is being misdiagnosed

The team is aligned on moving from fully manual writing to a scalable factory model where criteria can be generated, reviewed, tested, audited, and maintained at scale. But the organization is still treating the gap as if the only missing pieces are reviewer training or writer productivity.

### 1.2 This is not just a writer productivity problem

The team cannot move from *writing* to *reviewing* until output is actually reviewable. Today, a lot of "review" is still rewriting — writers are not just validating AI output, they are often:

- Finding the correct policy and additional relevant documents
- Reformatting and rewriting generated criteria
- Finding missing or ignored criteria, and removing criteria that shouldn't apply
- Creating and fixing extraction fields
- Working around eval limitations
- Testing manually and validating payer/source logic
- Managing customer feedback, POC support, and custom work

That is still production work. If output keeps getting pushed without fixing readiness, QC, payer mapping, eval testing, feedback capture, and ownership gaps, the team will scale the same hidden rework that created the current chaos. The immediate purpose of this plan is to reduce chaos, create visibility, and stop the team from absorbing missing infrastructure as personal failure.

---

# Part II — Roles: Ownership, Gaps, and How Each Is Measured

The future Criteria team isn't one generic group of "writers" — it needs distinct functions. These overlap near-term (pipeline output isn't consistently reviewable yet) and should separate more cleanly as it improves.

Each role below is a self-contained card: **what it owns, who has it today, the gap, the decision needed, and how it's measured** — so any one role can be answered at a glance without cross-referencing other chapters. Sorted by priority.

> 🚫 If the wrong payer, alias, plan category, or policy is used, the criteria output doesn't matter — **Payer Intelligence is upstream of everything else.**

---

### 🔴 Immediate Priority

**PjM / Program Control**
- **Owns:** Visibility, cadence, and follow-through across Qual — the command center: weekly updates, POC pipeline tracking, customer commitments, production reporting, owner/blocker/next-step visibility, escalation prep.
- **Status today:** Partial / split — Mary Cleary
- **Gap / risk:** In seat, but Bruna is still chasing status, blockers, commitments, and cross-functional fires.
- **Decision needed:** Reset daily/weekly reporting expectations and owner/blocker/next-step visibility.
- **Should own it:** Mary as Qual command center, or stronger operator support if cadence isn't met.
- **Measured by:** Weekly update completeness · daily report consistency · projects with owner/next step/due date · blockers surfaced · POC scope documented.

**Customer Feedback / Custom Criteria Owner**
- **Owns:** Feedback tickets, criteria corrections from live use, POC-specific needs, customer-specific rule adjustments, escalation to SMEs, closing the loop with customer-facing teams. **Executes**, doesn't just triage.
- **Status today:** Partial / split — Bruna Dos Santos, Tess L'Olivier-Lam
- **Gap / risk:** Tess and Bruna are overloaded; feedback/customer requests create SLA and people risk.
- **Decision needed:** Assign interim coverage and approve a dedicated owner.
- **Should own it:** Dedicated execution owner for feedback tickets, customer-specific changes, and custom criteria.
- **Measured by:** Tickets resolved · SLA performance · time to resolution · root cause · custom criteria completed · after-hours work required.

**Custom Criteria Execution**
- **Owns:** Customer-specific criteria execution and non-standard criteria work that doesn't fit the net-new production model.
- **Status today:** Partial / split — Bruna Dos Santos, Tess L'Olivier-Lam, Stacey Wisniewski
- **Gap / risk:** Custom work is hidden capacity, split across people with other responsibilities.
- **Decision needed:** Clarify whether this is combined with Customer Feedback or given separate execution allocation.
- **Should own it:** Customer Feedback / Custom Criteria Owner, with Criteria support as needed.
- **Measured by:** *Not separately defined yet* — currently folds into Customer Feedback / Custom Criteria Owner metrics above. Once the ownership decision above is made, this should get its own line so custom work doesn't hide inside feedback SLA numbers.

**Criteria QA Analyst / Auditor**
- **Owns:** Quality after criteria is written, generated, reviewed, or published: samples published criteria, owns the defect taxonomy, tracks recurring issues, decides review-tier movement, partners with Product/Eng on failure patterns.
- **Status today:** **Missing / new role** — nobody
- **Gap / risk:** No explicit QA owner; writers can't own production, review, QA, feedback, and pipeline improvement at once.
- **Decision needed:** Decide Stacey QA vs. team-lead tradeoff, or assign another QA owner.
- **Should own it:** Dedicated QA/Auditor owner; Stacey may fit only with a role tradeoff.
- **Measured by:** Criteria audited (coverage) · audit cadence met · critical defects found · escaped defects tracked · recurring patterns identified · rollbacks triggered appropriately · tier-movement recommendations · Product/Eng issues identified and fed back.

---

### 🟠 High Priority

**Payer Intelligence / Policy Mapping Owner**
- **Owns:** The payer/policy input layer: payer mapping, alias validation, hierarchy, policy rollups, public vs. portal-only tracking, no-policy payer tracking, coverage validation, tooling validation. Supports Qual, PAR, E&B, Sales scoping, and POCs.
- **Status today:** Ad hoc — Bruna Dos Santos, Mary Cleary, Tess L'Olivier-Lam
- **Gap / risk:** Fragmented/manual ownership; wrong payer or source invalidates criteria and scoping.
- **Decision needed:** Name owner and define payer intelligence scope.
- **Should own it:** Named owner responsible for source truth, mapping, tooling validation, and exceptions.
- **Measured by:** Payers validated · aliases validated · policy source confidence · mapping defect rate · exception resolution time.

**Criteria Writer — DME**
- **Owns:** Net-new DME criteria production, material rewrites, service-line package completion, and complex policy interpretation where AI output isn't yet reviewable.
- **Status today:** Exists — Jillian Poitras, Stacey Wisniewski, ShaMara Sanders, Justin Rydbom, Rachel Duda
- **Gap / risk:** High manual load; DME still requires human-owned writing/review; Jillian is split with BI/script work.
- **Decision needed:** Track DME by payer + plan category + service-line package, accounting for partial capacity.
- **Should own it:** Dedicated DME Criteria Writer function, measured by service-line package completion.
- **Measured by:** Criteria completed by work type · DME service-line packages completed (full payer + plan + service-line coverage credited, not just ticketed codes) · cycle time · major/critical defects after review · rework rate · blocker documentation · readiness movement · customer feedback due to a true policy defect. *Does not count against the writer:* feedback due to a customer business decision or a product/eval limitation.

**Criteria Writer / Reviewer — Infusions**
- **Owns:** Infusions criteria production, and supports the first controlled reviewer-mode pilot.
- **Status today:** Exists — Shannon Brown, Kali Sessions, Nicole Bright
- **Gap / risk:** Need capacity for 100% review *plus* the 30% shadow pilot before reducing review.
- **Decision needed:** Identify eligible payer/drug patterns and run the shadow pilot before operational review reduction.
- **Should own it:** Infusions Criteria team, with QA support for the 30% shadow pilot.
- **Measured by:** Same Writer metrics as DME above, plus — once in pilot — Reviewer metrics: drafts reviewed, review time, % approved as-is / with minor edits / requiring rewrite, defects caught by type, critical defects missed, reviewer agreement with QA.

**Vertical SME / Clinical Policy Consultant**
- **Owns:** Specialty ambiguity and clinical reasoning for DME, Fertility, Imaging, Orthotics, Wound Care, and future verticals.
- **Status today:** Partial / split — Bruna Dos Santos, Tess L'Olivier-Lam
- **Gap / risk:** Specialty work is ad hoc and not scalable as Fertility, Imaging, Orthotics, and Wound Care expand.
- **Decision needed:** Finalize specialty consultant path and escalation model.
- **Should own it:** Specialty SMEs or consultants with defined escalation paths and turnaround expectations.
- **Measured by:** Escalations resolved · turnaround time · criteria validated · reusable patterns created · specialty defects reduced.

**POC Support**
- **Owns:** POC support visibility, scope tracking, readiness, blockers, and next actions.
- **Status today:** Partial / split — Bruna Dos Santos, Tess L'Olivier-Lam
- **Gap / risk:** Unplanned and reactive — creates fire drills and hidden capacity drain.
- **Decision needed:** Create a POC tracker with scope, readiness, owner, blockers, and next action.
- **Should own it:** PjM / Program Control for tracking, with Feedback/Custom Criteria and Criteria owners for execution.
- **Measured by:** Active POCs · scope committed · readiness status · open questions · owner · next action. *(Thinner than other roles — worth a dedicated performance table once the tracker above exists.)*

**Internal Qual Tooling Support**
- **Owns:** Internal Qual tooling needs the Criteria team relies on to operate.
- **Status today:** Ad hoc — Bruna Dos Santos
- **Gap / risk:** Scrappy tools are becoming business-critical and are currently maintained ad hoc by operators.
- **Decision needed:** Assign Product/Engineering ownership.
- **Should own it:** Product/Engineering owner for tooling Criteria relies on.
- **Measured by:** Bulk test availability · packet test coverage · defects tied to pipeline runs · manual workaround reduction.

**Qualifications × Customer Training**
- **Owns:** Qualifications / customer training, education, and enablement loops.
- **Status today:** Exists — Tess L'Olivier-Lam
- **Gap / risk:** Tess owns too many adjacent loops and is pulled into execution work.
- **Decision needed:** Protect Tess's education role by removing feedback/custom execution burden where possible.
- **Should own it:** Tess, protected from execution burden by the Customer Feedback / Custom Criteria owner.
- **Measured by:** *Not yet defined* — flagged gap. Education-gap volume from the feedback taxonomy (§6) is the natural input metric once tracked.

---

### 🟡 Medium Priority

**Criteria Reviewer**
- **Owns:** Reviews AI-generated criteria output — structure, policy logic, extraction fields, doc requirements, code rules, quantity rules, downstream usability. Only works once output is good enough to *review* instead of *rewrite*.
- **Status today:** Partial / split — Bruna Dos Santos, Stacey Wisniewski
- **Gap / risk:** Review isn't cleanly separated from writing because output often still needs rewrite.
- **Decision needed:** Separate the reviewer role only once AI output is consistently reviewable.
- **Should own it:** Dedicated reviewer role once AI output is consistently reviewable.
- **Measured by:** AI-generated criteria reviewed · review time · % approved as-is · % approved with minor edits · % requiring material rewrite (mainly a pipeline signal, not a reviewer-speed signal) · defects caught by type · critical defects missed (should be near zero) · reviewer agreement with QA · customer feedback after reviewer approval (needs root-cause tagging before counting against the reviewer).

**BI Script Support**
- **Owns:** BI script support that currently consumes capacity from criteria-related roles.
- **Status today:** Partial / split — Jillian Poitras, Tess L'Olivier-Lam
- **Gap / risk:** Split capacity makes Jillian/Tess look more available for criteria work than they are.
- **Decision needed:** Account for BI/script support in capacity planning.
- **Should own it:** Separate BI/script support allocation, not counted as full criteria capacity.
- **Measured by:** *Not yet defined* — flagged gap.

**Data Labeling / QC Support**
- **Owns:** Data labeling and QC support work that supports Autopilot and evaluation quality.
- **Status today:** Exists — Chanda Woodruff, Christie Shade
- **Gap / risk:** Needs a clear lane so data labeling isn't confused with criteria writing/review.
- **Decision needed:** Keep labeling/QC support distinct from Writer and Reviewer roles.
- **Should own it:** Dedicated Data / QC support lane.
- **Measured by:** *Not yet defined* — flagged gap.

**Library Management**
- **Owns:** Library quality, criteria organization, and maintenance patterns that support reusable criteria.
- **Status today:** Partial / split — Bruna Dos Santos, Stacey Wisniewski
- **Gap / risk:** Split with other responsibilities; library quality may become a scale blocker.
- **Decision needed:** Clarify whether library management belongs under QA, production, or a separate owner.
- **Should own it:** Clear owner if library quality is critical to Criteria Factory scale.
- **Measured by:** *Not yet defined* — flagged gap.

---

# Part III — How Criteria Moves & When Review Changes

## 2. The Shared Workflow & Coverage Readiness

### 2.1 The Shared Workflow

Every piece of criteria — manual, AI-assisted, customer-specific, or pipeline-generated — should move through the same stages:

1. **Policy/source identified** — correct payer, source, policy, plan category, and relevant docs identified
2. **Draft generated or manually created**
3. **Written, rewritten, or reviewed** — human determines usable / needs edits / needs rebuild
4. **Extraction fields created or validated** against how documentation actually appears
5. **Human reviewed** — policy logic, structure, and usability validated
6. **Packet tested** where available — real or synthetic packets
7. **Ready for customer use** — internally approved for scoped use
8. **Live or live with limitations**
9. **Audited** — QA checks published/reviewed criteria and trend patterns
10. **Reworked** if defects, policy changes, or feedback require it

### 2.2 Coverage Readiness Statuses

Stop treating criteria as binary (built vs. not built). "Generated" ≠ "ready." "Reviewed" ≠ "tested." "Live" should never mean half-baked or unsupported.

| Status | Definition |
|---|---|
| Not started | Work has not begun |
| Policy sourced | Policy/source documents identified |
| Draft generated | Initial draft exists (pipeline or manual) |
| Human reviewed | Reviewed for policy logic, structure, usability |
| Packet tested | Tested against real or synthetic packets where available |
| Ready for customer use | Internally approved for scoped customer use |
| Live with limitations | Usable, but known limitations/unsupported areas remain |
| Live | Active and validated for the scoped use case |
| Needs rework | Requires rework due to defect, feedback, failed packet test, mapping issue, or policy change |

This creates a more honest view of coverage and supports phased rollout — e.g., going live with 80–85% of customer volume while the remainder moves through readiness states.

## 3. Review Tier Model

The goal isn't to reduce review for speed — it's to prove where reduced review is *safe*, where human review adds value, and where pipeline output still needs work. **Tiers move based on quality data, not calendar dates or gut feel.**

| Tier | Applies When | Human Involvement |
|---|---|---|
| **Tier 1 — 100% Review** | New payer/drug/service line, first time hitting a payer, open feedback ticket, high-risk or complex logic, shared criteria block, new specialty vertical, known payer mapping uncertainty, no packet testing available | Writer or senior reviewer reviews all output before publish |
| **Tier 2 — 30% Sampling Review** | Established payer/drug or payer/service-line pattern, clean prior review history, no recent critical defects, validated policy source & payer mapping, consistently structured output, rollback triggers defined | QA samples output and escalates defects; shared criteria blocks may stay at 100% even as code-specific criteria moves to sampling |
| **Tier 3 — 0% Pre-Publish Review** | Low risk, clean historical review/audit data, validated source & mapping, has passed the write → review → test loop, QA audit cadence exists, rollback triggers defined | QA audits post-publish on a defined cadence |

**A pattern can move from 100% → 30% review only when:**
- Payer and policy source are validated
- No unresolved critical defects exist
- Reviewed samples show a low non-critical defect rate
- Extraction fields are validated against packets where available
- Required vs. relevant documents are structured correctly
- Shared criteria blocks are reviewed and confirmed
- Customer feedback shows no recurring issues
- QA has a defined rollback trigger

**Work moves back to 100% review (rollback) when:**
- A critical defect is found
- Customer feedback shows recurring issues
- Payer mapping / source policy is questioned
- Packet testing fails
- Shared criteria is found to be wrong
- A downstream eval issue creates false pass/fail risk

**Piloting the model (Infusions first):**
1. Run the proposed 30% sample review
2. Still complete 100% review in the background
3. Compare what the 30% sample caught vs. what full review found
4. Track missed defects by severity
5. Decide whether the pattern can actually move to 30% sampling
6. Move failed patterns back to 100% review

Also needed to make testing real: (1) EHR lift from existing runs so reviewers can test against real documents, (2) synthetic packet generation for each priority drug/payer pattern, (3) a structured, de-identified packet-sourcing process.

### 3.1 DME: Near-Term vs. Future-State

**Stage 1 — Near-Term DME Operating Model** *(begins after the Comfort sprint)*

The immediate change is **not** moving DME to reviewer-only mode — it's moving DME away from isolated ticket work and into **service-line package** work.

> 📦 The right unit of work is: **payer + plan category + all codes for a given service line.**

When already inside a policy, complete the full service line even if only some codes were originally ticketed. For example: if a payer policy contains 35 codes in a service line and only 8 were originally ticketed, completing all 35 should be tracked and credited as completed coverage. Otherwise, we undercount real output and create duplicate future work.

Each DME service-line package should include: payer, plan category, service line, all applicable codes, shared criteria, code-specific criteria, quantity rules, policy source, alias mapping (where available), required documents, relevant/supportive documents, medical record timeframe (where required), known exclusions, and customer-specific overrides.

DME still requires human-owned writing and review in the near term because: pipeline output isn't consistently usable yet, payer mapping/alias support isn't stable, shared criteria blocks carry high propagation risk, eval testing is still manual with limited document access, and DME policies often require multi-document synthesis.

**Stage 2 — Future-State DME Review Model** *(not the immediate post-Comfort model)*

Moves from human-owned writing toward AI-assisted generation, service-line review, QA sampling, and eventually lower-review paths for low-risk work — once reliable payer mapping, alias support, policy source validation, service-line package generation, eval testing, QA ownership, defect tracking, a Product/Eng feedback loop, stronger shared-criteria safeguards, and reliable multi-document synthesis are in place.

---

# Part IV — Measurement System

## 4. Measurement Principles & Metric Layers

### 4.1 Principles

📏 This is the most important control layer in the plan. We need to stop using one productivity expectation for all criteria work — a writer on net-new complex DME criteria isn't doing the same job as a reviewer sampling established Infusions output, or an auditor checking system safety, or a feedback owner resolving a customer-specific business decision.

**We also need to stop measuring factory success by output alone.**

> ✅ We'll know the factory is working when throughput increases *without* increasing rework, defects, customer feedback, SLA misses, or after-hours effort.

Core questions this needs to answer: Is AI output becoming more reviewable? Are reviewers adding value? Is 30% review enough for the selected pattern? Is DME safe to reduce review? Is QA catching escaped defects and recurring patterns? Is payer mapping improving? Is Product/Engineering shipping the pieces that unlock scale? Is customer feedback decreasing or getting easier to resolve? Are we actually closer to a factory, or just pushing more manual work through people?

*(For role-specific metrics — what a Writer, Reviewer, QA Analyst, etc. is individually measured on — see each role's card in Part II. The layers below are cross-cutting: they feed those role metrics rather than duplicating them.)*

### 4.2 Layer 1 — Pipeline Productivity Metrics (ML/Product-tracked)

Jobs completed · Cumulative completed jobs · Time from kicked-off → review-ready → published · Editing time · No-edit rate · Changed/added/deleted/edited counts · Manual rules created · Number of order types generated · Number of codes/service lines covered · Number of criteria reopened after publish.

*Answers:* Is the pipeline producing more output? Is it becoming easier to review? Where is rework happening? Are writers/reviewers spending less time editing over time?

### 4.3 Layer 2 — AI Output Quality Metrics

Tracked separately from human performance, since writers are currently reviewing AI output.

| AI Output Quality | Meaning |
|---|---|
| Reviewable | Can be validated with little to no structural change |
| Reviewable with cleanup | Mostly usable, needs minor edits |
| Partially usable | Some useful content, but material rewrite needed |
| Not reviewable | Cannot be safely reviewed; needs to be rebuilt |
| Wrong source/payer | Tied to wrong payer, alias, plan category, or policy |
| Missing major logic | Missed important policy requirements or exceptions |
| Structurally unusable | Organized in a way that can't be evaluated correctly |

*Answers:* Is generated output becoming more reviewable over time? Which output types still require material rewrite? Are failures caused by AI quality, payer mapping, extraction field design, schema limitations, or source policy issues? When can the reviewer role separate from the writer role?

### 4.4 Layer 3 — Criteria Quality Dimensions

Criteria quality isn't fully binary — it has qualitative dimensions, since the same criteria may be policy-backed but not operationally usable for every customer, workflow, or document set.

| Dimension | Question |
|---|---|
| Policy fidelity | Did we capture the policy correctly and completely? |
| Applicability | Did we apply the right criteria to the right code, service line, payer, and plan category? |
| Operational usability | Can this work against real customer documentation? |
| Extraction quality | Are extraction fields complete, flexible, and aligned to how docs actually appear? |
| Customer/context fit | Does this match customer workflow, payer behavior, and implementation context? |

### 4.5 Layer 4 — Customer & Operational Metrics

Feedback ticket volume · SLA misses · Time to resolution · Reopened criteria · Customer-specific custom criteria requests · POC support hours · After-hours work required · Root cause of feedback · Owner responsible for resolution · Customer impact.

This is especially important for feedback/custom criteria work, since current SLA performance is being propped up by unsustainable after-hours effort.

### 4.6 Reporting by Work Type

A different cut than the role cards in Part II — this groups by *type of work* rather than *who's doing it*, useful for a weekly rollup.

| Work Type | What We Report |
|---|---|
| Net-new criteria | Criteria completed, codes/service lines covered, cycle time, blocker reason, rework required |
| AI draft + full review | Draft acceptance rate, % rewritten, review time, defects by type, extraction field issues |
| Sampling review | Sample size, defects found, severity, whether sampling was sufficient |
| QA audit | Published criteria audited, escaped defects, recurring patterns, rollback recommendations |
| Customer feedback / custom criteria | Ticket volume, SLA performance, time to resolution, root cause, owner, customer impact |
| Payer intelligence | Payers mapped, aliases validated, policy source confidence, mapping defects found |
| DME service-line packages | Packages completed, codes covered, incremental codes gained beyond ticketed work, shared criteria reused |
| POC support | Active POCs, scope committed, readiness status, open questions, owner, next action |

## 5. Customer Feedback & Defect Taxonomy

Customer feedback can *look* like "criteria is wrong," but not all feedback means the same thing — some is a true criteria defect, some a business decision, some a preference, some an education gap, some caused by payer mapping, product behavior, eval limitations, or workflow. **If we don't separate these, writer/reviewer metrics will be wrong and the team will keep treating every customer change as a criteria quality failure.**

### 5.1 Feedback Type → Meaning → Routing

| Feedback Type | Meaning | Counts as Criteria Defect? | Route To |
|---|---|---|---|
| True criteria defect | Tennr criteria is wrong against the source policy | Yes | Criteria ticket |
| Customer business decision | Customer agrees/understands but wants different handling | No | Custom criteria ticket |
| Customer disagreement | Customer disagrees with Tennr's interpretation | Needs review | Criteria review / SME review |
| Education gap | Criteria is correct, but explanation is missing/unclear | No | Enablement / Tess |
| Product/eval limitation | Criteria may be right, but the product can't evaluate it correctly today | No | Product/Eng |
| Payer/source issue | Wrong payer, alias, plan category, or policy source used | No — payer intelligence issue | Payer Intelligence |
| Workflow/config mismatch | Criteria may be right, but customer workflow/implementation doesn't support it | No, unless criteria needs to change | Implementation/Product |
| Documentation issue | Criteria depends on docs the customer doesn't have or labels differently | Sometimes | Criteria ticket only if doc flexibility needs to change |

**The key distinction to preserve:** *"The criteria was wrong"* is different from *"the criteria was reasonable/policy-backed, but the customer wants to operate differently."* Track these separately:

| Category | How to Interpret |
|---|---|
| Policy defect | Criteria was wrong against source policy — counts against quality |
| Operational usability issue | Technically right, but doesn't work well against customer docs/workflow — counts as product/process learning |
| Customer business decision | Customer agrees/understands but wants a different operational choice — not a defect, but does count as custom work |
| Customer disagreement | Customer disagrees with interpretation — needs SME/policy review; may or may not become a defect |
| Education gap | Criteria is correct but the explanation was missing/unclear — counts as an enablement gap |

### 5.2 Customer Feedback Outcomes

| Outcome | Meaning |
|---|---|
| Agree with criteria / no change needed | Customer reviewed and accepts the logic/output |
| Agree with criteria, but business decision to change | Customer understands the criteria is policy-backed but wants different handling |
| Disagree with criteria logic | Customer believes criteria is wrong or incomplete |
| Needs clarification / education | Customer doesn't understand why criteria is written this way |
| Workflow/configuration mismatch | Right criteria, wrong fit for customer workflow/setup |
| Product/eval limitation | Right criteria, can't be evaluated correctly today |
| Payer/source issue | Wrong payer, policy, alias, plan category, or source |
| Documentation issue | Depends on docs the customer doesn't have / labels inconsistently / can't provide |
| Open criteria ticket | Feedback requires actual criteria work |

### 5.3 Should a Ticket Open?

| Feedback Type | Ticket? |
|---|---|
| Agree / no change | No |
| Needs clarification / education | No criteria ticket — maybe an enablement note |
| Business decision change | Yes — custom criteria ticket |
| Disagree with criteria logic | Yes — criteria review ticket |
| Product/eval limitation | Product ticket, maybe a criteria workaround ticket |
| Payer/source issue | Payer intelligence ticket |
| Workflow/config mismatch | Implementation/Product ticket |
| Documentation issue | Criteria ticket only if document flexibility needs to change |

This avoids dumping everything into "criteria tickets."

### 5.4 Defect Types & Severity

**Severity:** Critical · Major · Minor · Preference

**Defect types:** Wrong policy used · Missing policy · Payer mapping issue · Alias/plan category issue · Missing required criteria · Incorrect criteria included · Shared criteria issue · Code-specific exception missed · Quantity rule issue · Required vs. relevant document issue · Extraction field issue · Medical record timeframe issue · Formatting/structure issue · Eval limitation · Customer-specific configuration issue · Specialty/clinical logic issue

**Every defect should tie back to:** pipeline run, source policy, payer/plan category, prompt/version, criteria output, reviewer correction, defect type, defect severity, and whether the root cause was criteria logic, extraction field design, eval limitation, payer mapping, or customer preference. Reviewer edits shouldn't just patch one criteria set — they should feed the loop that improves the factory.

### 5.5 Customer Criteria Feedback Form (intake — target: fillable in under 2 minutes)

| Field | Options / Format |
|---|---|
| Customer | Text / relation |
| Payer | Text / relation |
| Plan category | Medicare / Medicaid / Commercial / Unknown |
| Code / order type | Text |
| Criteria link | URL |
| Feedback source | Customer / AP / ESE / Implementation / Internal QA / Other |
| Feedback type | Agree, business decision change, disagree, clarification, workflow mismatch, product/eval limitation, payer/source issue, documentation issue |
| Customer position | Agree with Tennr / Disagree with Tennr / Unsure / Needs explanation |
| Is a criteria change needed? | Yes / No / Unsure |
| Should a ticket be opened? | Yes / No / Needs triage |
| Severity | Critical / Major / Minor / Preference |
| Customer impact | Blocking go-live / Blocking autopilot / Causing false pass-fail / Education only / No immediate impact |
| Requested change | Short text |
| Tennr assessment | Policy-backed / Customer preference / Needs research / Product limitation / Payer mapping issue |
| Owner | Person |
| Status | New / Triage / In Progress / Waiting on customer / Resolved / No change |
| Root cause | Criteria defect / Customer preference / Business decision / Payer mapping / Product limitation / Eval limitation / Education / Documentation |
| Final resolution | Changed criteria / No change / Opened product issue / Customer educated / Escalated |

## 6. Tracking System & Database Design

To operationalize the above, five lightweight databases are recommended:

**1. Criteria Work Items** *(the main tracker)*
Criteria/work item · Work type (net-new write, AI review, DME package, feedback, custom, QA audit) · Service line · Payer · Plan category · Owner (writer/reviewer) · Role performing work · Generated by AI? · AI output quality · Current stage (draft generated, reviewed, packet tested, live) · Readiness status (ready, live with limitations, needs rework) · Priority · Blocker (payer mapping, policy source, docs, Product/Eng, capacity) · Due date · Defect count (rollup) · Critical defect flag · Customer feedback count · Open tickets count · Final status · Notes

**2. AI Output Review Log**
What the writer/reviewer saw from the pipeline: related criteria · reviewer/writer · AI output quality · approved as-is? · minor edits? · material rewrite? · wrong payer/source? · missing policy logic? · extraction field issue? · review time · defects caught · escalation needed. *(This is how pipeline quality gets measured.)*

**3. Customer Feedback Log**
Customer · related criteria · feedback type · customer position · is change needed? · should ticket open? · severity · root cause · requested change · Tennr assessment · final resolution. Populated directly from the intake form in §5.5.

**4. Criteria Tickets**
Ticket · related feedback · related criteria · ticket type (criteria defect / custom criteria / payer mapping / product limitation / education / implementation) · owner · priority · SLA · status · resolution.

**5. Defect / QA Audit Log**
Defect · related criteria · found by (reviewer, auditor, customer, eval) · severity · defect type · root cause (pipeline, human error, payer mapping, eval limitation, customer-specific) · owner · status (open, fixed, validated) · customer impact flag · Product/Eng needed flag · rollback needed? · tier movement recommendation.

**The clean operating loop these support:**
1. AI generates criteria → 2. Writer/reviewer reviews AI output → 3. Output is approved, rewritten, escalated, or blocked → 4. Criteria moves into a readiness status → 5. Customer/internal feedback is captured in structured form → 6. Feedback becomes: no change, education, custom criteria, criteria defect, payer issue, product issue, or implementation issue → 7. QA audits whether writer/reviewer/pipeline process worked → 8. Metrics tell us whether AI output, human review, or customer acceptance is improving.

**Readiness pipeline metrics to track from this system:** # not started · # policy sourced · # draft generated · # human reviewed · # packet tested · # ready for customer use · # live with limitations · # live · # needs rework.

---

# Part V — Dependencies & Resourcing

## 7. Product / Engineering Dependencies

The Criteria Factory target assumes several foundational pieces are available. They are not. The team can keep increasing manual throughput, but the factory transition depends on Product/Engineering delivering these:

| Dependency | Why It Matters | Success Metric | What It Unlocks |
|---|---|---|---|
| Bulk packet testing from user-generated output packets | Required to prove criteria works against real documents | % criteria tested against packets; pass/fail by extraction field | Readiness status, review-tier movement, extraction validation |
| Eval harness / bulk testing | Required to safely improve prompts and models | Ability to compare old vs. new criteria/model output | ML/Product can iterate without blind risk |
| Defect logging tied to pipeline runs | Turns review into system feedback | % defects tied to source/prompt/output | Improves generation and prioritizes tooling work |
| Payer mapping / alias tooling | Prevents wrong payer/policy criteria | Mapping confidence, alias validation rate, mapping defect rate | Reduces wrong-payer criteria, scoping errors, reporting inaccuracies |
| Service-line package generation | Required for the DME model | Packages generated by payer + plan + service line | Enables DME scale beyond isolated code tickets |
| Approved AI tooling / Claude wrapper | Current workarounds are too fragile and compliance-sensitive | Supported workflow available to the criteria team | Lets the team use the strongest tooling safely |
| Internal Qual tooling ownership | Current tools are becoming business-critical but remain scrappy/ad hoc | Named Product/Eng owner; reduced manual workaround use | Moves critical tooling out of one-off maintenance by operators |
| Criteria schema improvements | Needed for complex criteria patterns | Reduction in manual restructuring / workaround criteria | Supports and/or logic, relevant vs. required docs, timeframes, variables, inheritance, negative policies |

> ⭐ **The single highest-leverage ask: a path for bulk testing criteria against user-generated output packets.** Without it, we cannot define whether criteria is safe to reduce review, know if extraction fields work, measure false pass/fail, improve underlying Qual prompts safely, prove whether generated criteria is operationally usable, or move from subjective expert confidence to measurable readiness.

## 8. Specialty Vertical Support Needs

### Fertility

Fertility criteria are not structured like standard DME or Infusions criteria — the challenge isn't just whether the patient meets clinical criteria, but how services are *packaged, authorized, and paid*. Fertility policies often involve clinical pathways, age limits, prognosis, infertility duration, prior treatment, diagnosis history, ART/IVF requirements, donor vs. autologous cycle rules, contraindications, genetic testing, cycle limits, and plan-specific benefit restrictions. Services may be bundled into a larger fertility/IVF cycle, so criteria may need to be written at the cycle, procedure, lab, medication, or benefit level.

**Key questions to resolve before scaling:** What is the correct unit of authorization? Is the service bundled or separately authorized? What codes belong together? Which services need standalone criteria vs. inheriting from a broader cycle? What documentation is required vs. supportive? Which exclusions/contraindications should fail criteria? Is coverage driven by medical necessity, fertility benefit structure, pharmacy benefit, or mandate-specific rules?

Without fertility expertise, we risk overbuilding criteria for bundled services, missing criteria for standalone services, misrepresenting plan-specific coverage, or misrouting work between Qual, Prior Auth, benefits verification, and customer configuration. **The goal isn't just to write fertility criteria — it's to understand how fertility services are clinically qualified, packaged, authorized, and paid so the right criteria model gets built from the start.**

### Imaging

Imaging criteria are fundamentally different from DME criteria. DME revolves around equipment need, documentation presence, diagnosis support, quantity limits, and medical necessity tied to a specific item/service line. Imaging is driven by clinical indication, prior treatment, prior imaging, symptom progression, red flags, conservative therapy, and whether the requested study is appropriate for the patient's condition. Many imaging policies are also written as **exclusionary/negative policies** — broadly allowing imaging for many indications, then defining what is *not* covered — which requires a different evaluation approach than checking for a diagnosis on a list.

**What imaging support needs to define:** sufficient clinical indications, documentation patterns that support medical necessity, what prior imaging/treatment matters, hard requirements vs. supporting context, how to handle negative policies and exclusions, how to distinguish clinical criteria from utilization-management guidance, and how to test criteria against real imaging documentation. Without imaging expertise, we risk over-writing criteria, adding too much context, or creating brittle logic the tool can't evaluate correctly.

*(Orthotics and Wound Care are also named specialty verticals needing SME/consultant coverage as they expand — see the Vertical SME card in Part II.)*

---

# Part VI — Execution

## 9. Roadmap

### Next 2 Weeks — Establish the operating control layer
- Define metrics by work type
- Expand the COE database with coverage, bandwidth, owner, gap, decision, priority, and metrics fields
- Define Coverage Readiness statuses
- Define critical vs. non-critical defect taxonomy
- Define what "safe to reduce review" means
- Define review-tier movement rules and rollback triggers
- Identify the first Infusions shadow pilot group
- Define a weekly reporting template by work type
- Reset Mary's PjM cadence: daily production/status report-out, weekly Qual project update, POC pipeline visibility, customer commitment tracker, owner/blocker/next-step tracker
- Assign interim coverage for customer feedback/custom criteria work
- Decide the Stacey QA vs. team-lead tradeoff
- Define the Payer Intelligence owner scope
- Hire or finalize VGM consultants for DME escalation support
- Research and shortlist consultants for Fertility and Imaging
- Define how DME will be tracked post-Comfort at the payer + plan category + service-line level

### Next 30 Days — Launch controlled experiments and create visibility
- Launch the Infusions 30% shadow pilot; continue 100% review in the background for the pilot group
- Compare sampled defects vs. full-review defects
- Track defect rate, rewrite rate, review time, packet-test pass rate, and escaped defects
- Start coverage readiness reporting and weekly reporting by work type
- Start customer feedback/custom criteria SLA reporting
- Start the payer/order type cleanup process
- Begin DME service-line package tracking post-Comfort; track incremental DME codes gained beyond originally ticketed work
- Build a Product/Engineering dependency table with status, owner, sequencing, success metric, what it unlocks, and risk if not shipped
- Confirm the Fertility and Imaging consultant path

### Next 60 Days — Graduate only where quality data supports it
- Move selected Infusions patterns to true 30% sampling **only if shadow data supports it**; move failed patterns back to 100% review
- Add a QA audit cadence for published criteria
- Use defect data to improve pipeline prompts, extraction field standards, and payer mapping process
- Operationalize the payer intelligence function
- Continue the DME service-line package model; define shared criteria review requirements for DME
- Begin formal Fertility and Imaging criteria model development with consultant input
- Review whether customer feedback/custom criteria SLA performance has improved with dedicated ownership or interim coverage
- Reassess capacity against actual work-type reporting instead of total output alone

## 10. Alignment Summary

1. **Criteria Factory is not just a productivity problem.** Output matters, but isn't enough — we need to measure readiness, quality, rework, customer feedback, SLA performance, and after-hours effort.
2. **Review reduction must be data-based**, not calendar-based. Tiers move on defect data, packet testing, and mapping/QA confidence.
3. **DME moves to service-line package tracking before reduced review.** Post-Comfort, DME moves to payer + plan category + service-line tracking — that does *not* mean reduced human review yet.
4. **Missing operating functions need to be resourced:** strong PjM, Customer Feedback/Custom Criteria Owner, Criteria QA/Auditor, Payer Intelligence Owner, Specialty SMEs/consultants, and Product/Engineering support for internal Qual tooling.
5. **Product/Engineering dependencies need ownership.** Factory velocity is now constrained less by writer effort and more by internal tooling iteration speed.

**What this plan does, end to end:**

1. Stabilize current production and reduce chaos.
2. Move DME from isolated ticket work to payer + plan category + service-line package tracking after Comfort.
3. Separate net-new criteria production from customer feedback and custom criteria execution.
4. Protect Tess's education role by adding dedicated bandwidth for feedback/custom criteria execution.
5. Define Coverage Readiness so "generated," "reviewed," "tested," and "live" aren't conflated.
6. Define quality metrics, customer feedback categories, defect taxonomy, and review-tier movement rules.
7. Pilot reviewer-mode in Infusions through a shadow experiment before reducing review operationally.
8. Use quality data to graduate work into lower-review tiers.
9. Build the QA and Payer Intelligence functions so review, audit, and payer/policy mapping are owned explicitly.
10. Add DME, Fertility, and Imaging specialty support before scaling those areas further.
11. Use defect data and packet testing to improve the generation pipeline instead of relying on one-off manual fixes.
12. Tie factory-level velocity expectations to actual readiness across tooling, payer mapping, packet testing, QA, customer feedback, and staffing.

---

# Appendix A — Weekly Signal Log

⚠️ **Living, append-only. Not part of the static plan above — this is where real weeks get tested against the principle in §4.1, so a record-output week doesn't get read as a pure win if it was bought with unsustainable effort. Add new rows as weeks come in; don't fold this back into the plan body.**

| Date | Observation | What It Means Against the Framework |
|---|---|---|
| Week of June 30, 2026 | Highest-throughput week yet, but achieved through massive effort. The backlog has shifted almost entirely into **policy research** and **reviewing writer output**. Actual workflow: writer drafts with Claude → output goes into Tennr (pipeline) → writer makes edits → writer uses Claude again to review the edited output → **Bruna is still catching errors on personal review**, on top of both AI touchpoints. | **Does not clear the bar in §4.1.** Throughput went up, but so did effort — this is not evidence the factory is working, it's evidence the team is absorbing more load at Tier 1 (100% review), which is still fully justified. Several distinct signals here, not one: (1) policy research eating the backlog points at the Payer Intelligence gap (Part II, Part V §7), not a writer-capacity problem — research is upstream of writing. (2) Errors surviving *two* AI touchpoints (draft + AI-assisted review of the edited output) and still getting caught by Bruna's manual pass means AI-assisted review is not yet a reliable substitute for expert review — Bruna's layer can't be thinned even as more AI review gets added. This supports keeping the pattern at Tier 1 and argues for QA/Auditor ownership (Part II) so what human review is catching gets tracked as data instead of disappearing into "personal review." |
