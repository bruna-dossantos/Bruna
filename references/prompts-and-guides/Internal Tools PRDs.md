# Qual Internal Tools — PRDs
## PRD Sheet Database: https://www.notion.so/tennr/eaa8db77c5794e6bab48d8522d44ae5e

---

# 1. PRD: AI Feedback Loop for Criteria Review
**Area:** Draft Criteria | **Priority:** P0 | **Status:** Drafted

> **Goal:** Give criteria reviewers a structured, lightweight way to flag errors in a Qual run and have the system translate that feedback into targeted, human-reviewable edits to extraction fields and/or criteria — without auto-applying any change.

### Background

When a reviewer finds that Qual made the wrong call on an order, the feedback loop today is entirely manual: write a note, ping the COE, and a writer reverse-engineers what went wrong. There is no structured path from "the model got this wrong" to "here is a proposed fix."

Multiple high-risk accounts have raised this directly. Broadway Home Medical's lead validator reported spending an hour on 3 Qual checks partly because feedback had no structured channel. The Nunns CX escalation in March 2026 traced criteria drift to the absence of a reliable feedback loop. Liberator's DTC team cited inability to adjust criteria as a blocker to adoption. Feedback today lives in Slack, Salesforce risk tickets, and ad-hoc COE conversations — none of it traceable to a specific criteria version or extraction field.

### Problem Statement

Reviewers have no structured mechanism to flag specific failure modes in a Qual run. Feedback is unstructured, untraceable, and manually triaged. Criteria writers cannot confidently accept or reject a change suggestion because there is no provenance — who saw what, in which version, and what the proposed fix should be.

### Goals

- Give reviewers four structured feedback types tied to specific extraction fields or criteria.
- Allow reviewers to highlight a supporting snippet in the source document and tag it to a criterion.
- Route each piece of feedback automatically to: **Fix Extraction**, **Fix Criteria**, or **Needs More Info in Docs**.
- Always produce a before/after diff — never auto-apply.
- Maintain a full audit log: reviewer, version, document, feedback type, proposal, and writer decision.

### Non-Goals

- Auto-applying any suggestion without a writer's explicit acceptance.
- A full rules engine or policy interpretation layer.
- Retroactively updating previously rendered qualification decisions.

### Users

- **Criteria reviewers / data labelers** — need fast, low-friction controls to flag what went wrong.
- **COE / criteria writers** — need a clear diffed proposal to accept or reject, not a freeform Slack message.
- **Engineering / product** — need a traceable schema to build monitoring on (failure rates by type, payer, code).

### Proposed Solution

**Reviewer Feedback Controls**

For each Qual run result, reviewers see a compact feedback panel with four action types:

1. **Not found (false negative)** — field should have been extracted but wasn't. Ties to one or more extraction fields.
2. **Found but shouldn't count (false positive)** — field was extracted but is incorrect. Marks the specific extraction.
3. **Should not qualify** — marks an incorrect qualification. Optional structured reasons (e.g., "Criterion A was met but B was not").
4. **Should qualify** — marks an incorrect non-qualification.

Reviewers can also highlight a snippet from the source document and tag it to a specific criterion label.

**Feedback Routing**

Every submission is automatically bucketed: **Fix Extraction**, **Fix Criteria**, or **Needs More Info in Docs**. The system generates a before/after diff of the specific field or criterion for writer review.

**Writer Review Flow**

Writers see a queue of pending suggestions. Each shows: the before/after diff, reviewer's feedback with highlighted snippet, criteria version under review, and reviewer identity. Accept or reject — nothing deploys without explicit acceptance.

**Audit Log**

Every feedback event records: reviewer, timestamp, version, document/order reference, feedback type, routing bucket, proposed change, and writer decision.

### Requirements

**Functional**
- Reviewers can submit structured feedback on any Qual run result.
- System auto-routes feedback to the correct bucket.
- System generates a before/after diff for the specific field or criterion.
- Nothing auto-deploys; writers explicitly accept or reject.
- Full audit trail on every event.

**UX**
- Feedback controls are low-friction — no long forms.
- Diff view clearly distinguishes before vs. after.
- Writer queue is filterable by payer, code, feedback type, and routing bucket.

**Observability**
- Track feedback volume by type, routing bucket, payer, and criteria version.
- Alert on high false-positive or false-negative rates for a given code or payer.

### Rollout Plan

1. **Phase 1** — Structured feedback controls + routing buckets. No suggestions yet — structured intake replacing Slack/Salesforce freeform.
2. **Phase 2** — System-generated diff proposals for writer review.
3. **Phase 3** — Audit log dashboard + observability metrics.

### Open Questions

- Should feedback be visible to customers, or COE-internal only?
- Should the system suggest the edit automatically (LLM-generated) or only surface the feedback for a human writer to draft the fix manually?
- What is the minimum version of this that unblocks the highest-volume feedback use cases?

### Success Metrics

- Reduction in unstructured Slack/Salesforce feedback threads for criteria issues.
- Time from feedback submission to accepted fix.
- Reviewer adoption rate (% of review sessions using structured feedback).
- Reduction in repeat errors for the same criterion after a fix is accepted.

---

# 2. PRD: AND/OR Logic in Criteria Editor
**Area:** Draft Criteria | **Priority:** P1 | **Status:** Drafted

> **Goal:** Enable criteria authors to express AND/OR grouping logic within a single criteria block, starting with one level of branching.

### Background

Today, criteria in QualHub is authored as a flat, linear checklist. There is no way to express "A AND (B OR C)" within a single criteria block. When a policy has branching requirements — for example, one qualification pathway for COPD and a different one for OSA on the same HCPCS code — writers must create separate order types entirely. This has compounding costs: more order types to maintain, more payer mappings to configure, and greater risk of drift when the underlying policy changes.

The Nationwide customer implementation surfaced this directly: Bruna flagged in December 2025 that routing to specific order types by payer was necessary because creating separate order types for every insurance would create the same load-time and maintenance problems seen at Liberator. AND/OR logic within a criteria block would reduce the need to split order types just to express conditional qualification pathways.

### Problem Statement

Criteria authors cannot express branching logic within a single criteria block. The only available workaround is creating separate order types — which multiplies maintenance burden and increases the risk of criteria drift across copies.

### Goals

- Enable criteria authors to define AND/OR groupings within a criteria block.
- Support at minimum one level of nesting (v1); multiple levels of branching in a future version.
- Preserve existing flat criteria behavior — no migration required for existing blocks.
- Preview/validation: authors can see how logic will evaluate before deploying.

### Non-Goals

- A full-featured rules DSL or conditional expression engine (v2+).
- Customer-facing editing of AND/OR logic (COE authoring only, v1).
- Auto-generating branching logic from policy PDFs.

### Users

- **COE / criteria authors** — need to express nuanced multi-path policies without creating duplicate order types.
- **Engineers** — need a clean data model that supports rendering branching logic in the qualification worker.

### Proposed Solution

**Authoring Experience**

In the criteria editor, authors can group criteria into AND/OR blocks:
- **AND group**: all criteria within this group must be met.
- **OR group**: at least one criterion within this group must be met.

Groups are visually distinct in the editor (indentation, labeled brackets, or collapsible blocks).

**V1 Scope: One Level**

A single level of AND/OR nesting covers the most common policy patterns:
- "(A AND B) OR (C AND D)" — two AND-groups joined by OR.
- "A AND (B OR C)" — a top-level AND with one OR branch.

**Rendering Behavior**

The qualification worker evaluates grouped criteria according to the defined AND/OR logic. The result shows which branch was satisfied (for audit and reviewer context).

**Preview**

Authors can preview how the logic evaluates against a sample document before deploying.

### Data Model

Extend the criteria schema to support:
- `criteria_group`: type (AND | OR), ordered list of child criteria or child groups.
- `criteria_item`: existing single criterion.
- Groups are recursively nestable but limited to depth 1 in v1.

### Requirements

**Functional**
- Authors can create AND/OR groups in the criteria editor.
- V1 supports one level of nesting.
- Existing flat criteria render identically (no breaking changes).
- Qualification worker evaluates AND/OR logic correctly.
- Audit trail records which branch was satisfied.

**UX**
- Groups are visually distinct and not confusing alongside flat criteria.
- Preview mode lets authors validate logic before deploy.

### Rollout Plan

1. **Phase 1** — Data model + backend support for one-level AND/OR groups.
2. **Phase 2** — Editor UI for creating and editing groups + preview.
3. **Phase 3** — Multi-level nesting (v2).

### Success Metrics

- Reduction in duplicate order types created solely to express branching qualification pathways.
- Author-reported time to express a multi-path criteria policy.
- Zero regression in existing flat criteria evaluation accuracy.

---

# 3. PRD: Bulk Edit Tool for Criteria
**Area:** Draft Criteria | **Priority:** P1 | **Status:** Drafted

> **Goal:** Enable COE and engineering teams to perform bulk operations across order types — with preview, rollback, and audit trail — without one-by-one manual edits.

### Background

The team currently has no bulk editing capability. When a payer policy changes, a code limit updates, or a criteria pattern needs to be corrected across all of a customer's order types, each order type must be edited individually. This is a significant time sink for the COE team and is one of the reasons the criteria backlog grows faster than it can be worked down.

The automated "Outdated Order Types Notice" bot message (visible in #ops-tennr-criteria-management) already fires when order types fall behind — but the remediation is still entirely manual per order type. The Nunns situation, where criteria drifted to V2 vs. the current V14, is a direct consequence of no bulk update path existing. The bulk edit tool is listed as a dependency for the Criteria Dashboard (Source of Truth).

### Problem Statement

There is no bulk operation path for criteria. Any update that touches multiple order types — even a simple find-and-replace or criteria toggle — requires individually opening and editing each one, with no preview or rollback safety net.

### Goals

- Enable bulk operations across order types, filtered by customer/payer/code/service line.
- Require preview before applying: authors must see what will change before committing.
- Rollback: ability to undo a bulk operation after the fact.
- Audit trail: every bulk action is logged with operator, timestamp, scope, and change summary.

### Non-Goals

- Real-time collaborative editing (covered separately by the locking/editing-by feature in Criteria Dashboard).
- Bulk operations on criteria logic (AND/OR, variable substitution) — those are v2 once the underlying features are built.
- Customer-facing bulk operations.

### Users

- **COE / ESE teams** — need to apply consistent updates across many order types without per-order-type effort.
- **Criteria writers** — need confidence that a bulk action will do what they expect before it's applied.

### Proposed Solution

**Filter**

Users define the scope of a bulk operation using filters:
- Customer org
- Payer / payer family
- Service line
- HCPCS code or code family
- Criteria version range (e.g., "all order types on versions < v14")

**Operation Types (v1)**

- **Find and replace** — replace a specific text string across all criteria in scope.
- **Add criteria** — append a new criterion to all order types in scope.
- **Remove criteria** — remove a specific criterion by label from all order types in scope.
- **Update criteria text** — replace the full text of a criterion matching a label across scope.

**Preview**

Before committing, users see:
- Count of order types affected.
- Side-by-side diff for a sample of affected order types.
- Option to exclude specific order types from the operation.

**Apply + Rollback**

- One-click apply after preview confirmation.
- Rollback available for a defined window (e.g., 30 days) or until the next edit on any affected order type.

**Audit Trail**

Every bulk operation is logged: operator, timestamp, filter scope, operation type, count of affected order types, and rollback status.

### Requirements

**Functional**
- Filter scope by customer/payer/code/service line.
- Preview shows diff before apply.
- Rollback available post-apply.
- Full audit log per bulk operation.

**UX**
- Filter UI is clear about what's in scope before preview.
- Preview step is mandatory — no skip.
- Rollback is surfaced prominently in the audit log.

### Dependency

Criteria Dashboard (Source of Truth) — bulk edit surfaces are most useful when combined with the drill-down and filtering capabilities in the Criteria Dashboard.

### Rollout Plan

1. **Phase 1** — Find-and-replace + add/remove criteria. Preview + apply. Audit log.
2. **Phase 2** — Rollback capability.
3. **Phase 3** — Additional operation types (bulk criteria version sync, bulk toggle).

### Success Metrics

- Time to apply a payer-wide criteria update (before vs. after).
- Reduction in manual per-order-type edits for known bulk updates.
- Rollback usage rate (proxy for preview usefulness and error rate).
- Zero incidents of unintended criteria changes from bulk operations.

---

# 4. PRD: Qualification Payer Mapping (Routing Payer vs. Coverage Policy)
**Area:** Draft Criteria | **Priority:** P0 | **Status:** Drafted

> **Goal:** Introduce a distinct "qualification payer" concept that separates clearinghouse routing identity from medical necessity / coverage policy identity, so that criteria can be configured once and reused across multiple routing payers that share the same coverage guidelines.

### Background

Tennr currently models payer identity based on the Stedi clearinghouse routing / e-claim ID. This works for claim submission. However, Tennr also uses this same payer identity for qualification criteria, authorization rules, and medical necessity lookups — which is incorrect.

Insurance providers intentionally consolidate clearinghouse routing while decentralizing medical policy. For example, AARP UHC (Medicare), UHC Commercial, UHC Community Plan Ohio (Medicaid), and UHC Community Plan Kansas (Medicaid) all route through the same Stedi ID (87726), but have completely different qualification criteria. UHC Community Plan Ohio requires prior authorization for J1453 and J1627; UHC Community Plan Kansas does not. Tennr currently treats them as one payer for criteria purposes.

This causes two failure modes:
1. **Wrong criteria applied** — a patient's commercial plan gets Medicare criteria or vice versa.
2. **Criteria duplication** — to work around the problem, teams create separate order types for each routing payer, multiplying maintenance burden.

Additional complexity: many payers require applying guidelines from a parent company or Medicare even when the "payer on the card" is a different brand. BCBS out-of-state scenarios require routing medical necessity to the home plan rather than the local plan.

### Problem Statement

Tennr conflates two distinct concepts — clearinghouse routing identity and coverage policy identity — in a single payer record. This causes incorrect criteria application and forces teams to create duplicative order types to work around it.

### Goals

- Introduce a **qualification payer** concept that is separate from the routing payer.
- Enable many-to-one criteria mapping: multiple routing payers can point to one shared qualification payer (and thus one shared set of criteria).
- Enable home vs. local plan routing for medical necessity using E&B data.
- Ensure payer type (Medicare, Medicare Advantage, Medicaid MCO, Commercial) is a first-class attribute on the qualification payer, not derived from the routing ID.

### Non-Goals

- Replacing Stedi for claim routing — routing payer is unchanged.
- Auto-detecting the correct qualification payer from E&B data without configuration.
- Customer-facing payer configuration.

### Users

- **COE / criteria writers** — need to configure criteria against a qualification payer once, not per routing payer.
- **ESE / implementation teams** — need a clear mapping interface to connect routing payers to qualification payers.
- **Qual worker** — needs to resolve the correct qualification payer at runtime using E&B data and routing payer.

### Proposed Solution

**Two-Layer Payer Model**

1. **Routing Payer** — Stedi/EDI ID. Used for clearinghouse submission only. Unchanged.
2. **Qualification Payer** — A separate entity representing a specific coverage policy context (plan type + state + issuer). Used for criteria lookup, authorization rules, and medical necessity.

**Mapping**

- Many routing payers can map to one qualification payer.
- Mapping is configured per customer org.
- E&B home vs. local plan data can be used to dynamically select the correct qualification payer at runtime (when home ≠ local plan).

**Qualification Payer Attributes**

- Canonical name (e.g., "UHC Community Plan Ohio (Medicaid MCO)")
- Plan type: Medicare / Medicare Advantage / Medicaid MCO / Commercial / Other
- State (for Medicaid MCOs and state-specific commercial plans)
- Parent payer reference (optional, for policy inheritance)

**Many-to-One Criteria**

In the criteria editor, criteria are authored against qualification payers. A single qualification payer's criteria can be referenced by any number of routing payers — no duplication needed.

### Requirements

**Functional**
- Qualification payer is a distinct entity from routing payer.
- Routing payer → qualification payer mapping is configurable per org.
- Many routing payers can map to one qualification payer.
- Qual worker resolves qualification payer at runtime before criteria lookup.
- Home vs. local plan E&B signal can drive qualification payer selection.

**UX**
- Mapping interface is clear and does not require engineering support for standard configurations.
- Mismatches between routing payer and qualification payer are surfaced as warnings, not silent failures.

### Open Questions

- What is the migration path for existing order types already configured against routing payer IDs?
- Should qualification payer be a workspace-level or org-level entity?
- How do we handle payers where policy inheritance is multi-level (e.g., MCO → State Medicaid → Medicare)?

### Rollout Plan

1. **Phase 1** — Data model: qualification payer entity + routing payer mapping. No UI yet; engineering-configured.
2. **Phase 2** — Mapping UI for COE/ESE. Criteria editor switches to qualification payer.
3. **Phase 3** — Home vs. local plan runtime resolution from E&B data.

### Success Metrics

- Reduction in duplicate order types created to work around routing payer conflation.
- Zero incidents of wrong criteria applied due to routing payer conflation (post-launch).
- Time to configure a new payer's criteria after launch vs. before.

---

# 5. PRD: Order Type Attributes & Filtering
**Area:** Organization / Clean Up | **Priority:** P1 | **Status:** Drafted

> **Goal:** Add structured, filterable attributes to order types — payer, service line, code family, customer — so that authors and ESEs can find, manage, and operate on order types efficiently.

### Background

Order types today have no structured metadata beyond their name. Finding a specific order type in a customer org requires scrolling or searching by name — there is no filter by payer, service line, or code family. This creates operational friction for every team that works with order types: COE writers, ESEs managing customer configs, and anyone trying to scope a bulk operation or understand what's in a customer's library.

This is also a blocker for the Bulk Edit Tool, which requires filtering by customer/payer/code/service line to define the scope of a bulk operation.

### Problem Statement

Order types lack structured attributes. There is no reliable, UI-surfaced way to filter them by payer, service line, code family, or customer. This makes QualHub harder to navigate at scale and blocks filtering-dependent features like bulk edit.

### Goals

- Define a standard set of structured attributes on order types: payer, service line, code family, customer.
- Make all attributes filterable in the order type browser.
- Attributes are set at authoring time and editable post-creation.
- Attributes are available as filter inputs for the Bulk Edit Tool.

### Non-Goals

- Free-tagging or custom attribute creation by customers.
- Auto-populating attributes from criteria content (v2).

### Users

- **COE / criteria writers** — need to find order types by payer, code, or service line quickly.
- **ESE / implementation teams** — need to filter a customer's order type library by payer or service line during setup and maintenance.
- **Bulk Edit Tool** — consumes attributes as filter inputs.

### Proposed Solution

**Standard Attribute Set (v1)**

| Attribute | Type | Notes |
|---|---|---|
| Payer / Payer Family | Select (multi) | Links to qualification payer when available |
| Service Line | Select | From the org's service line list |
| Code Family | Select | E.g., DME, Infusion, Imaging |
| Customer | Derived | Set from parent org context |

**Filter UI**

In the order type browser, a filter panel allows filtering by any combination of attributes. Filter state is shareable (URL params or saved views).

**Editing**

Attributes are set during order type creation and editable afterward. Editing an attribute does not change criteria content.

### Requirements

**Functional**
- Standard attribute fields on every order type.
- All attributes are filterable in the browser.
- Attributes are available as inputs to the Bulk Edit Tool.
- Editing attributes does not affect criteria or version history.

**UX**
- Filter panel is visible without scrolling.
- Multi-select on payer/code family for complex filter combinations.
- Clear visual distinction between filtered and unfiltered state.

### Rollout Plan

1. **Phase 1** — Attribute schema + data migration for existing order types (with defaults).
2. **Phase 2** — Filter UI in order type browser.
3. **Phase 3** — Attribute-based inputs in Bulk Edit Tool.

### Success Metrics

- Time to find a specific order type in a large customer library (before vs. after).
- Adoption of attribute-based filters by COE and ESE teams within 30 days.

---

# 6. PRD: Search & Filter Within Order Types
**Area:** Organization / Clean Up | **Priority:** P2 | **Status:** Drafted

> **Goal:** Add text search and structured filtering within the order type browser so authors and ESEs can find specific order types, criteria, and codes without scrolling.

### Background

At scale, a customer org can have hundreds of order types. There is currently no search functionality within the order type list or within the criteria inside an order type. Finding a specific criterion or code requires manual scrolling. This is a day-to-day friction point for every criteria writer and ESE.

### Problem Statement

There is no search or filter capability within the order type browser or within individual order type criteria. As library size grows, navigation becomes untenable.

### Goals

- Full-text search across order type names, criteria labels, and criteria content.
- Filter by order type attributes (depends on Order Type Attributes feature).
- Search within a single order type's criteria by label or content keyword.

### Non-Goals

- Semantic / AI-powered search (v2).
- Cross-customer search.

### Users

- **COE / criteria writers** — need to find criteria by keyword without opening every order type.
- **ESE teams** — need to quickly find the right order type during customer setup.

### Proposed Solution

**Global Search (within org)**
- Search bar in the order type browser returns order types whose name, payer, criteria labels, or criteria content match the query.
- Results show: order type name, matched criteria label/snippet, and payer context.

**Inline Search (within order type)**
- Search bar within an open order type's criteria panel.
- Highlights matching criteria labels or text.

### Requirements

**Functional**
- Full-text search across order type names and criteria content within an org.
- Inline search within a single order type.
- Search works in conjunction with attribute filters (from Order Type Attributes).

### Rollout Plan

1. **Phase 1** — Inline search within a single order type.
2. **Phase 2** — Global search across the org's order type library.

### Success Metrics

- Reduction in time to find a specific criterion or order type.
- ESE and COE adoption within 30 days of launch.

---

# 7. PRD: Offerings & Service Lines — Capability Parity with Order Types
**Area:** Organization / Clean Up | **Priority:** P2 | **Status:** Drafted

> **Goal:** Bring Offerings and Service Lines to feature parity with Order Types — specifically: edit capability, structured attributes, insurance mapping, and archive.

### Background

Order Types have a well-developed toolset: editing, versioning, insurance mapping, archive capability, and attribute filtering (planned). Offerings and Service Lines are structurally similar entities but lack these capabilities. Authors who need to configure or manage content at the Offering or Service Line level are blocked or must work around the limitations by making changes at the Order Type level instead.

The Nunns CX escalation and J&B onsite feedback both surfaced service line configuration as a pain point — specifically the inability to manage insurance mapping and attributes at the service line level, and the difficulty of archiving outdated service lines.

### Problem Statement

Offerings and Service Lines lack the same set of management capabilities as Order Types. Authors cannot edit, attribute-filter, map insurance, or archive at the Offering or Service Line level.

### Goals

- Offerings and Service Lines support: edit, structured attributes, insurance mapping, and archive.
- Capabilities mirror what exists (or is planned) for Order Types.
- No regressions to existing Order Type behavior.

### Non-Goals

- New capabilities not already available on Order Types (covered separately).
- Customer-facing editing of Offerings or Service Lines.

### Users

- **COE / criteria writers** — need to manage Offerings and Service Lines with the same control they have on Order Types.
- **ESE teams** — need to configure insurance mapping and archive outdated Service Lines without engineering support.

### Proposed Solution

**Edit**
- Offering and Service Line names, descriptions, and metadata are editable post-creation.

**Structured Attributes**
- Same attribute set as Order Types: payer/payer family, code family, customer.
- Filterable in the Offering/Service Line browser.

**Insurance Mapping**
- Insurance mapping (qualification payer assignment) is configurable at the Service Line level, not just Order Type level.
- Order Types can inherit the Service Line's insurance mapping or override it.

**Archive**
- Service Lines and Offerings can be archived.
- Archive requires confirmation step.
- Archived entities are hidden from default views but accessible via filter.

### Rollout Plan

1. **Phase 1** — Edit + archive for Offerings and Service Lines.
2. **Phase 2** — Attributes + filtering.
3. **Phase 3** — Insurance mapping at Service Line level with inheritance model.

### Success Metrics

- Reduction in Order-Type-level workarounds for Service Line configuration tasks.
- ESE time to configure a new Service Line's insurance mapping (before vs. after).

---

# 8. PRD: Offerings Cleanup — Clear Boundaries Between Offerings, QualHub, and Internal Tools
**Area:** Organization / Clean Up | **Priority:** P1 | **Status:** Drafted

> **Goal:** Establish and enforce clear operational boundaries between Offerings, QualHub, and internal tooling, so authors always know where to do what.

### Background

Currently, there is meaningful confusion about what belongs in Offerings vs. QualHub vs. internal tools. Customer-specific configuration has drifted into QualHub, canonical names don't match writer workflows, and it is unclear what the authoritative source of record is for different types of content.

This confusion creates operational risk: authors make changes in the wrong place, customer-specific config overwrites shared templates, and the same content exists in multiple locations with no clear owner.

### Problem Statement

There are no enforced or clearly documented operational boundaries between Offerings, QualHub, and internal tools. Customer-specific configuration has leaked into QualHub, canonical names are inconsistent, and authors don't have a reliable mental model for where to do what.

### Goals

- Define and document the canonical purpose of each layer: Offerings, QualHub, internal tools.
- Ensure canonical names in QualHub match writer workflows and terminology.
- Move customer-specific configuration out of QualHub and into the appropriate org-level location.
- Enforce separation at the data model level where possible (not just via documentation).

### Non-Goals

- Restructuring the technical architecture of QualHub from scratch.
- Migrating all historical content in a single release.

### Users

- **COE / criteria writers** — need a clear mental model of where to author, store, and retrieve different types of content.
- **ESE teams** — need to know which layer is authoritative when configuring a customer.
- **Customers** — should never encounter Tennr-internal configuration in their org view.

### Proposed Solution

**Layer Definitions (to be documented and enforced)**

| Layer | Purpose | Owner |
|---|---|---|
| QualHub | Tennr-standard criteria library. No customer-specific content. | COE |
| Offerings | Productized bundles of QualHub content. Canonical names + service line structure. | COE / Product |
| Customer Org | Customer-specific configuration, overrides, and custom criteria. | ESE / Customer |

**Canonical Naming**
- QualHub entity names are reconciled with COE writer terminology (e.g., using "Medicare Criteria" not "Custom Criteria").
- Name changes are logged and communicated to affected teams.

**Customer-Specific Config Migration**
- Audit identifies all customer-specific configuration currently stored in QualHub.
- Migrations move config to the appropriate customer org, with clear documentation of what moved.

**Enforcement**
- System prevents saving customer-specific config (e.g., customer name fields, customer-specific payer overrides) at the QualHub level.

### Rollout Plan

1. **Phase 1** — Audit: identify all customer-specific content currently in QualHub.
2. **Phase 2** — Documentation: publish and distribute layer definitions + naming standards.
3. **Phase 3** — Migration: move customer-specific config to correct orgs.
4. **Phase 4** — Enforcement: system-level guardrails preventing future drift.

### Success Metrics

- Zero customer-specific config items remaining in QualHub post-migration.
- Author-reported clarity on "where to do what" (qualitative).
- Reduction in ESE escalations caused by config-layer confusion.

---

# 9. PRD: Move Customer-Specific Config Out of QualHub
**Area:** Organization / Clean Up | **Priority:** P1 | **Status:** Drafted

> **Goal:** Remove all customer-specific configuration from QualHub and relocate it to the appropriate customer org, establishing a clean separation between Tennr-standard and customer-specific content.

### Background

Customer-specific configurations have accumulated in QualHub over time — payer mappings, custom criteria overrides, and org-specific settings that should live in customer orgs instead. This creates confusion for writers who can't tell what's standard vs. custom, and risks unintended cross-customer contamination when a QualHub template is cloned.

### Problem Statement

Customer-specific configuration stored in QualHub pollutes the Tennr standard library, makes templates unreliable for cloning, and obscures the line between what Tennr owns and what a customer has customized.

### Goals

- Audit and identify all customer-specific content currently in QualHub.
- Migrate identified content to the correct customer orgs.
- Prevent future drift via system-level enforcement.

### Non-Goals

- Changing what customers are allowed to configure — only moving where it lives.
- Rebuilding the customer org infrastructure.

### Users

- **COE / criteria writers** — need QualHub to be a clean, reliable standard library.
- **ESE teams** — need customer orgs to be the single authoritative location for customer-specific config.

### Proposed Solution

**Audit**
Systematically identify all records in QualHub that contain customer-specific identifiers (customer name, org ID, customer-specific payer mappings).

**Migration**
Move each identified record to the correct customer org. For each migration:
- Document what was moved, from where to where, and when.
- Notify affected ESEs.

**Enforcement**
Add system-level validation that prevents customer-specific fields from being saved at the QualHub level going forward.

### Rollout Plan

1. **Phase 1** — Audit tooling: automated detection of customer-specific content in QualHub.
2. **Phase 2** — Manual review + migration execution.
3. **Phase 3** — System-level enforcement preventing future drift.

### Success Metrics

- Zero customer-specific config items remaining in QualHub post-migration.
- Zero regression in customer orgs post-migration (customer behavior unchanged).

---

# 10. PRD: Create Service Lines in Customer Orgs
**Area:** Organization / Clean Up | **Priority:** P1 | **Status:** Drafted

> **Goal:** Enable ESEs and COE to create net-new Service Lines directly within a customer org, without requiring engineering support.

### Background

Currently, Service Lines can only be cloned from QualHub into customer orgs. There is no ability to create a net-new Service Line from scratch within a customer org. When a customer has a product line or workflow that doesn't map to any existing QualHub Service Line, the team has no self-service path — it requires engineering involvement.

Bruna flagged this in the Nunns escalation in March 2026 as one of the items blocking customer-specific configuration from being properly managed.

### Problem Statement

ESEs and COE cannot create Service Lines from scratch within a customer org. All Service Lines must originate from QualHub clones, which doesn't accommodate genuinely customer-specific workflows.

### Goals

- Allow authorized users (COE / ESEs) to create net-new Service Lines within a customer org.
- New Service Lines support the full Order Type lifecycle within them.
- Clearly marked as "Customer-Specific" (not cloned from QualHub).

### Non-Goals

- Customers self-creating Service Lines without COE/ESE involvement.
- Auto-populating new Service Lines with criteria (v2).

### Users

- **ESE teams** — need to stand up customer-specific workflows without engineering tickets.
- **COE** — need the ability to create and own customer-specific Service Lines.

### Proposed Solution

Add a "Create new Service Line" action within the customer org interface. The creation flow captures:
- Service Line name and description.
- Code family association.
- Customer-specific flag (auto-set; not cloneable to QualHub).

The new Service Line supports all existing Order Type operations within it.

### Requirements

- Authorized users can create Service Lines directly in customer orgs.
- Created Service Lines are flagged as customer-specific.
- Customer-specific Service Lines cannot be promoted to QualHub without an explicit promotion workflow.

### Rollout Plan

1. **Phase 1** — Creation flow in customer org. Customer-specific flag.
2. **Phase 2** — Optional: promotion workflow to QualHub if a customer-specific line becomes a standard template.

### Success Metrics

- Reduction in engineering tickets to create customer-specific Service Lines.
- ESE self-service rate for new Service Line creation post-launch.

---

# 11. PRD: Clone Individual Codes or Order Types
**Area:** Organization / Clean Up | **Priority:** P2 | **Status:** Drafted

> **Goal:** Allow authors to clone a single code or individual order type — without pulling in the entire service line — preserving existing customizations.

### Background

Today, cloning in QualHub operates at the Service Line level. When an ESE or COE author wants to bring in a single order type or add a single code for a customer, they must clone the entire Service Line, which overwrites existing customizations or creates duplicates that then require cleanup.

This has caused operational issues: Bruna noted in #sku-qualifications-worker that the duplicate issue occurs specifically when a service line already exists in an org and is then cloned in again without deleting it first. Jasper confirmed that criteria don't populate correctly unless the writer makes a manual change and redeploys. Granular clone control would prevent these failure modes.

### Problem Statement

Cloning operates at the Service Line level only. Bringing in a single code or order type for a customer requires a full Service Line clone, which disrupts existing customizations and creates duplicate entities.

### Goals

- Enable cloning at the individual code or order type level (not just Service Line).
- Cloning preserves existing customizations in the destination org.
- Conflict detection: if an order type with the same code/payer already exists, surfaced before commit.

### Non-Goals

- Cross-customer cloning (within a customer's own org only, in v1).
- Merging customizations from two order types automatically.

### Users

- **ESE teams** — need to add a single new code to a customer's existing library without disrupting what's already there.
- **COE** — need to apply a single updated order type to a customer without a full service line re-clone.

### Proposed Solution

**Clone Controls**

From any Order Type in QualHub or an org, a "Clone to..." action appears. Users select:
- Destination org.
- Target Service Line within destination (or "create new").
- Conflict behavior: skip existing, overwrite, or cancel.

**Code-Level Clone**

From within an Order Type, individual codes can be cloned to a destination Order Type (same or different customer org).

**Conflict Detection**

Before committing, the system surfaces any existing order types in the destination with overlapping codes/payers and prompts the user to resolve.

### Requirements

- Clone action available at Order Type and code level.
- Destination selection (org + service line).
- Conflict detection before commit.
- Preserves existing customizations in destination (no silent overwrites).

### Rollout Plan

1. **Phase 1** — Order Type-level clone with conflict detection.
2. **Phase 2** — Code-level clone within an order type.

### Success Metrics

- Reduction in support tickets caused by Service Line re-cloning side effects.
- ESE time to add a single new code to an existing customer library.

---

# 12. PRD: No Reasoning in Extraction Prompts
**Area:** LLM Prompt Updates | **Priority:** P0 | **Status:** Drafted

> **Goal:** Block decision or reasoning language from appearing in extraction field prompts, ensuring extractions return only structured values rather than justifications.

### Background

Extraction fields in QualHub are designed to return structured values from source documents — a date, a diagnosis code, a yes/no, a quantity. However, extraction prompts have accumulated decision and reasoning language over time (e.g., "determine whether the patient qualifies based on..."). This causes the model to return explanatory text instead of structured values, which breaks downstream criteria evaluation and makes results harder to audit.

This is a data quality and reliability issue at the prompt level. The fix is both a tooling constraint (prevent reasoning language at authoring time) and a cleanup pass on existing prompts.

### Problem Statement

Extraction prompts contain reasoning/decision language that causes the model to return justifications instead of structured values, degrading extraction accuracy and breaking downstream evaluation.

### Goals

- Detect and flag reasoning/decision language in extraction prompts at authoring time.
- Block deployment of extraction fields with flagged language (or warn and require confirmation).
- Provide authors a clear pattern for what extraction prompts should look like vs. shouldn't.
- Optionally: automated cleanup suggestions for existing extraction prompts that contain flagged patterns.

### Non-Goals

- Changing the criteria evaluation logic or reasoning behavior in the qualification worker.
- Flagging reasoning in criteria fields (only extraction fields in scope for v1).

### Users

- **COE / criteria writers** — need clear authoring-time guidance and guardrails.
- **Engineering** — needs a reliable extraction schema: structured values, not freeform text.

### Proposed Solution

**Authoring-Time Detection**

When saving an extraction field prompt, the system scans for reasoning/decision language patterns:
- Phrases like "determine whether", "evaluate if", "consider", "based on the evidence", etc.
- Patterns that ask the model to make a qualification determination rather than extract a value.

**Guardrail**

- **Hard block**: prompts containing prohibited reasoning patterns cannot be deployed without a writer explicitly overriding (with justification logged).
- **Soft warn (v1)**: prompts trigger a warning with a specific explanation of the flagged pattern and a suggested rewrite.

**Style Guide**

A brief inline authoring guide distinguishes extraction prompts (return a value) from criteria prompts (evaluate a condition). Examples of good and bad patterns are shown in the editor.

**Cleanup Pass**

For existing extraction prompts: a one-time audit tool identifies all deployed extraction prompts containing flagged patterns. COE reviews and rewrites with guidance.

### Rollout Plan

1. **Phase 1** — Authoring-time soft warning + style guide in editor.
2. **Phase 2** — Hard block on deploy + override with justification.
3. **Phase 3** — Automated cleanup tooling for existing deployed prompts.

### Success Metrics

- Reduction in extraction fields returning freeform reasoning instead of structured values.
- Zero newly deployed extraction prompts with reasoning language (post-Phase 2).
- Extraction accuracy improvement for flagged codes post-cleanup.

---

# 13. PRD: Reuse & Learn from High-Quality Deployed Criteria (90%+ Threshold)
**Area:** LLM Prompt Updates | **Priority:** P1 | **Status:** Drafted

> **Goal:** Prompt the criteria generation model to reuse and learn from criteria already deployed above a 90% quality threshold, rather than generating from scratch each time.

### Background

Tennr has an accumulating library of deployed criteria with measured quality. Some criteria consistently perform above 90% accuracy across the packets tested against them. Currently, when a new criteria is authored — either by a writer or via the Policy Reporter pipeline — this institutional knowledge is not surfaced or incorporated. The model generates fresh, without awareness of what has already been proven to work.

The Policy Reporter pipeline already generates LLM-based revisions to initial criteria outputs (as noted in Spencer's July 2025 product update). The next step is systematically biasing generation toward high-quality proven patterns rather than starting from a blank slate.

### Problem Statement

The criteria generation pipeline does not incorporate institutional knowledge from high-performing deployed criteria. Writers and the LLM are repeatedly generating patterns that may already exist in tested, deployed form — creating unnecessary rework and inconsistency.

### Goals

- At criteria authoring time (manual or pipeline-generated), surface semantically similar criteria that are deployed above the 90% quality threshold.
- Prompt the model to use those high-quality examples as a primary reference before generating novel text.
- Reduce the incidence of near-duplicate criteria that are slightly different from high-performing deployed versions.
- Writers can accept a suggested match, modify it, or proceed with a novel draft.

### Non-Goals

- Auto-applying reused criteria without writer review.
- Defining what "90%" means or building the quality measurement system (assumed to exist).
- Cross-customer criteria sharing where criteria contain customer-specific language.

### Users

- **COE / criteria writers** — benefit from surfaced matches and faster authoring.
- **Policy Reporter pipeline** — benefits from reduced generation noise and higher first-draft quality.

### Proposed Solution

**Similarity Search at Authoring Time**

When a writer begins drafting a new criterion (or the pipeline generates a first draft), the system:
1. Embeds the draft criterion text.
2. Queries a vector index of deployed criteria above the 90% quality threshold.
3. Surfaces the top-N semantically similar matches, with their quality score and deployment context (payer, code, service line).

**Writer Interaction**

Writers see a "Similar deployed criteria" panel alongside the editor:
- Match text + quality score + context.
- "Use this" button: inserts the matched criterion into the editor.
- "Use as base" button: inserts as editable starting point.
- Dismiss: proceed with novel draft (logged for feedback loop).

**Pipeline Integration**

The Policy Reporter pipeline uses the similarity index as a retrieval step before generation. The system prompt includes top-N matches as few-shot examples.

### Requirements

- Vector index of deployed criteria above quality threshold, updated on new deployments.
- Similarity search available at authoring time and in the pipeline.
- Writer panel showing matches with quality context.
- Writer accept/modify/dismiss decision is logged.

### Rollout Plan

1. **Phase 1** — Build vector index of high-quality deployed criteria.
2. **Phase 2** — Surface matches in the criteria editor (writer-facing).
3. **Phase 3** — Integrate similarity retrieval into Policy Reporter pipeline generation step.

### Success Metrics

- Reduction in near-duplicate criteria (criteria created when a 90%+ match already existed).
- First-draft quality score of pipeline-generated criteria (before vs. after retrieval augmentation).
- Writer adoption rate of "Use this" / "Use as base" actions.

---

# 14. PRD: Unique Criteria Labels Enforcement
**Area:** LLM Prompt Updates | **Priority:** P1 | **Status:** Drafted

> **Goal:** Enforce unique criterion labels within a code at authoring time, flagging duplicates and near-duplicates before deployment.

### Background

Criteria labels are used as identifiers in the feedback loop, audit trail, and version diffing. Duplicate labels within a code create ambiguity: when a reviewer flags "Criterion A," it's unclear which one they mean. Near-duplicate labels (e.g., "Physician signature" and "Physician Signature") create silent noise in reporting and make automated feedback routing unreliable.

This is also a prompt hygiene issue: when the qualification worker processes multiple criteria with identical labels, evaluation results are ambiguous and difficult to trace.

### Problem Statement

Duplicate and near-duplicate criteria labels within a code are permitted at authoring time, creating downstream ambiguity in feedback, audit trails, and evaluation results.

### Goals

- At authoring time, detect and flag exact duplicate criterion labels within a code.
- Detect and flag near-duplicate labels (case-insensitive, whitespace-normalized, edit-distance threshold).
- Block deployment of criteria with duplicate labels (or require explicit override).
- Near-duplicates: surface as warnings, not hard blocks, in v1.

### Non-Goals

- Enforcing label uniqueness across codes or order types (within-code uniqueness only in v1).
- Auto-renaming duplicate labels.

### Users

- **COE / criteria writers** — need authoring-time feedback before deploying duplicate labels.
- **Feedback loop / audit systems** — depend on label uniqueness for reliable criterion identification.

### Proposed Solution

**Duplicate Detection**

When a writer saves a criterion label, the system checks for:
1. **Exact match** (case-insensitive): hard block.
2. **Near-match** (edit distance ≤ 2, or same words in different order): soft warning with suggested resolution.

**UI**

- Duplicate: red inline error. Cannot save without changing the label.
- Near-duplicate: yellow inline warning. Can dismiss and proceed (logged).

**Existing Criteria**

A one-time audit surfaces all existing duplicate/near-duplicate label pairs by code. COE resolves with guidance.

### Rollout Plan

1. **Phase 1** — Detection + hard block on exact duplicates at authoring time.
2. **Phase 2** — Near-duplicate soft warning.
3. **Phase 3** — Audit tool for existing deployed duplicates.

### Success Metrics

- Zero newly deployed criteria with duplicate labels within a code (post-Phase 1).
- Reduction in reviewer-reported label ambiguity in feedback.

---

# 15. PRD: Policy Metadata & Provenance
**Area:** Policy Reporter Pipeline | **Priority:** P0 | **Status:** Drafted

> **Goal:** Ensure every policy object in the system carries full provenance — payer-authored date, Tennr-authored date, and a required source URL or document ID.

### Background

Tennr is building toward a criteria process that is auditable and defensible. A core requirement for auditability is knowing *which* policy a criterion was written against, *when* that policy was authored by the payer, and *when* Tennr authored the corresponding criterion.

Today, neither of these dates is consistently captured. Criteria are authored without a required link to the source policy document or URL. This means Tennr cannot tell whether a criterion is based on a policy that has since been updated, and cannot demonstrate to a customer or payer that a criterion was based on a specific policy version at a specific date.

Bruna flagged policy provenance as a core requirement in the Halftime meeting statement — the criteria process must be auditable and defensible, not just functional.

### Problem Statement

Policy objects lack provenance metadata. There is no reliable record of which payer policy a criterion was derived from, when the payer last updated it, or when Tennr authored the criterion against it. This makes criteria indefensible in audits and prevents reliable detection of when a criterion is based on an outdated policy.

### Goals

- Every policy object carries: payer-authored date, Tennr-authored date, and a required source URL/document ID (or explicit "custom" designation).
- Source link is required before criteria can be deployed (or a "custom / no policy" override is selected).
- Provenance is visible in the criteria editor and in the audit trail.

### Non-Goals

- Automatically fetching and validating payer policy URLs (v2).
- Section-level mapping within a source document (covered in Policy Link → Section-Level Mapping PRD).

### Users

- **COE / criteria writers** — need to record and see provenance when authoring.
- **ESE teams** — need to point customers to the source policy when criteria are questioned.
- **Audit / compliance** — needs full provenance trail for every deployed criterion.

### Proposed Solution

**Policy Object Fields**

Add the following required fields to every policy object:

| Field | Required | Notes |
|---|---|---|
| Payer-authored date | Required | Date the payer last published/updated this policy |
| Tennr-authored date | Auto-set | Date the Tennr criterion was created/last modified |
| Source URL | Required (or "custom") | URL to the payer's published policy document |
| Document ID | Optional | Internal reference if sourced from Policy Reporter pipeline |
| Custom flag | Alternative to source URL | Used when no published policy exists |

**Authoring Enforcement**

Source URL or "custom" selection is required before a criteria can be published/deployed.

**Display**

Provenance metadata is visible:
- In the criteria editor (below the criteria text).
- In the audit trail entry for each deployment.
- In the Criteria Dashboard drill-down (when built).

### Rollout Plan

1. **Phase 1** — Add provenance fields to schema. Soft enforcement (warning on deploy without source).
2. **Phase 2** — Hard enforcement: source URL or "custom" required before deploy.
3. **Phase 3** — Backfill tooling for existing deployed criteria.

### Success Metrics

- % of deployed criteria with provenance metadata (target: 100% for new criteria from Phase 2).
- Reduction in "which policy is this based on?" questions to COE from ESE/CX teams.

---

# 16. PRD: Revision Flags & Policy Change Notifications
**Area:** Policy Reporter Pipeline | **Priority:** P0 | **Status:** Drafted

> **Goal:** When a payer policy updates, automatically highlight what changed and alert impacted criteria owners so Tennr's criteria don't silently fall out of date.

### Background

Payer policies update regularly. Today, there is no automated mechanism to detect when a payer has updated a policy and flag the Tennr criteria that were authored against the previous version. The COE team relies on manual monitoring — checking Policy Reporter, reading bulletins — to detect policy changes. Criteria can remain deployed against an outdated policy for weeks or months before anyone notices.

Policy Reporter is already integrated and used as the source for payer policy content. The Policy Reporter Pipeline channel in Slack shows active usage. The missing layer is an automated change-detection and alerting workflow on top of what Policy Reporter already delivers.

### Problem Statement

Payer policy changes are not automatically surfaced to criteria owners. Criteria can remain deployed against outdated policies indefinitely, creating compliance, accuracy, and audit risk.

### Goals

- When a payer policy updates in Policy Reporter, automatically detect the change and produce section-level deltas.
- Alert the criteria owner(s) whose criteria reference the updated policy.
- Apply a "Needs Review" flag to affected criteria where Tennr's interpretation is older than the payer's latest policy date.
- Alert routing: targeted notifications (not broadcast) to the specific criteria owner.

### Non-Goals

- Auto-updating criteria in response to policy changes (human review required).
- Monitoring policies not in Policy Reporter (external monitoring is out of scope for v1).

### Users

- **COE / criteria writers** — need targeted alerts when policies they've authored against are updated.
- **Stacey / criteria team leads** — need visibility into the aggregate backlog of "needs review" criteria.

### Proposed Solution

**Change Detection**

When Policy Reporter delivers a new version of a payer policy:
1. System compares against the previous stored version.
2. Produces section-level diff (added, removed, modified sections).
3. Identifies all Tennr criteria linked to the updated policy (via source URL / document ID from Policy Metadata).

**"Needs Review" Flag**

Criteria whose source policy has been updated are automatically flagged as "Needs Review." The flag shows:
- Policy updated date.
- Section(s) that changed.
- Which criteria may be affected (linked to the delta).

**Alert Routing**

Criteria owners receive a targeted notification (in-app or Slack) when one of their criteria's source policies has been updated. Notification includes:
- Payer name + policy name.
- What changed (section summary).
- Link to the criteria flagged for review.

**Aggregate View**

Criteria team leads see a dashboard of all "Needs Review" criteria, filterable by payer, owner, and age of flag.

### Requirements

**Functional**
- Automated change detection when a policy version is updated in Policy Reporter.
- Section-level diff generation.
- "Needs Review" flag applied to affected criteria.
- Targeted notification to criteria owner.
- "Needs Review" flag clears when a criteria owner reviews and confirms/updates the criterion.

### Rollout Plan

1. **Phase 1** — "Needs Review" flag on criteria when source policy is updated. Manual review to clear.
2. **Phase 2** — Section-level diff display in criteria review flow.
3. **Phase 3** — Targeted notifications to criteria owners.

### Success Metrics

- Time from payer policy update to criteria owner awareness (before vs. after).
- % of criteria reviewed and updated within 30 days of a policy change notification.
- Reduction in deployed criteria based on policies updated > 90 days ago without review.

---

# 17. PRD: Required Policy Link → Section-Level Mapping
**Area:** Policy Reporter Pipeline | **Priority:** P1 | **Status:** Drafted

> **Goal:** Require every criterion to link to a specific section of its source policy document before deployment, creating traceable, section-level provenance.

### Background

The Policy Metadata PRD establishes that every criterion must link to a source URL or document. This PRD goes one level deeper: the link should point to a specific *section* within that document, not just the document root.

This matters for two reasons:
1. **Auditability** — when a criterion is challenged, the COE can point to exactly which section of the payer's policy supports it.
2. **Change detection precision** — revision flags (see Revision Flags PRD) are more useful if they know which section of the policy a criterion maps to, rather than just the document. Section-level delta detection is only reliable when section-level mapping exists.

### Problem Statement

Criteria link to source policy documents at best, but not to specific sections. This makes audits imprecise and limits the usefulness of automated policy change detection.

### Goals

- Each criterion references a specific section of its source policy document (section name, page, or anchor).
- Section reference is required before deploy (or explicit override for documents without sections).
- Section reference is visible in the criteria editor and audit trail.
- Section-level mapping feeds into the Revision Flags change-detection system.

### Non-Goals

- Automated section extraction from policy documents (v2).
- Requiring section references for "custom" criteria with no published source policy.

### Users

- **COE / criteria writers** — need a lightweight way to record the section reference without it being a major friction point.
- **Audit / compliance** — needs section-level traceability.
- **Revision Flags system** — consumes section references for targeted change detection.

### Proposed Solution

**Section Reference Field**

In the criteria editor, alongside the source URL field, a "Section reference" field accepts:
- Free-text section name/number (e.g., "Section 4.2 — Coverage Criteria").
- Page number (for PDF documents without named anchors).
- Auto-populated anchor if Policy Reporter provides section metadata.

**Enforcement**

- Required before deploy (soft warning in Phase 1, hard block in Phase 2).
- Exception: "custom" flag on the policy object bypasses section requirement.

**Display**

Section reference shown in:
- Criteria editor (below source URL).
- Audit trail entries.
- Criteria Dashboard drill-down.

### Rollout Plan

1. **Phase 1** — Section reference field (optional). Auto-populate from Policy Reporter where available.
2. **Phase 2** — Soft enforcement: warning on deploy without section reference.
3. **Phase 3** — Hard enforcement + section reference feeds Revision Flags.

### Success Metrics

- % of newly deployed criteria with section-level references (target: 100% for new from Phase 3).
- Reduction in time to locate the supporting policy section when a criterion is challenged.

---

# 18. PRD: Criteria Dashboard (Source of Truth)
**Area:** Source of Truth | **Priority:** P0 | **Status:** Drafted

> **Goal:** Create a single place to see what's live, in draft, being edited, what changed, and what's impacted — with full drill-down from code to every order type, service line, and customer where it is used.

### Background

There is no single view of the criteria system's state. Writers, ESEs, and team leads have to navigate across QualHub, customer orgs, Linear tickets, and Slack threads to piece together what is live, what is being edited, and what is impacted by a given change.

The absence of this view has real operational cost. The Nunns escalation (March 2026) was triggered in part because no one had a clear picture of which order types had drifted, by how much, and who owned them. Bruna directly linked multiple customer escalations to this gap in the #post-nunns thread — including criteria dashboard, version history, and outdated order type flagging — all of which are sub-features of this PRD.

Jasper confirmed in #sku-qualifications-worker that versioning work is underway (Versioning pt 2), and the Criteria Dashboard is the home for surfacing that data to the broader team.

### Problem Statement

There is no unified view of the criteria system's state. The team cannot answer "what is live, where is it used, who is editing it, and what has changed" without significant manual investigation.

### Goals

**Drill-Down Navigation**
- Code → every order type, service line, and customer where it is used.
- Order Type → every service line and customer where it is used.
- Service Line → every customer where it is used.

**Staging States**
- Clear visual states: Draft → Editing → Deployed.
- "Currently Being Edited By [name]" visible at all times (locking / edit presence).

**Locking**
- Prevent concurrent overwrites.
- Lock is visible to all viewers; locked entity shows who holds the lock and when they started.
- Lock is released on save/discard or via force-release by an admin.

### Non-Goals

- Replacing the criteria editor — this is a read/navigate/triage surface, not an authoring surface.
- Customer-facing criteria visibility (internal only in v1).

### Users

- **COE / criteria writers** — need to see what's live and what's being edited without stepping on each other.
- **Stacey / criteria team leads** — need an operational view of the whole library's health.
- **ESE teams** — need to answer "what criteria does this customer have deployed" without asking COE.
- **Bruna / leadership** — need a high-level view of criteria coverage and health across the library.

### Proposed Solution

**Dashboard Home View**

Filterable table/card view of all criteria entities (codes, order types, service lines) showing:
- Current staging state (Draft / Editing / Deployed).
- Last edited by + timestamp.
- "Currently Being Edited By" indicator (live presence).
- # of customers using this entity.
- Policy metadata (source URL, payer-authored date, "Needs Review" flag if applicable).

**Drill-Down**

From any entity, click to see every downstream consumer:
- Code → all order types that include this code → all service lines and customers using those order types.
- Order Type → all service lines → all customers.
- Service Line → all customers.

**Edit Presence / Locking**

When a writer opens an entity for editing:
- The entity is marked "Being Edited By [name]" across all views.
- Other users see the lock and are prevented from concurrent editing (or directed to a merge/coordination flow).
- Lock releases on save, discard, or admin force-release.

### Sub-Features (separate PRDs or phases)

- **Stable Version History** — full version/history view per entity.
- **Custom vs. Source Tracking** — every order type marked as cloned or custom.
- **Customer Toggle with Audit Trail** — customer on/off with confirmation.
- **Flag When Out of Date from Parent** — visual indicator on cloned entities behind their parent.

### Requirements

**Functional**
- Unified view of all criteria entities with staging state.
- Drill-down from code to customers.
- Edit presence / locking mechanism.
- Policy metadata and "Needs Review" flag visible.

**UX**
- Fast to load even at scale (hundreds of order types per customer, dozens of customers).
- Filter by customer, payer, service line, staging state, "Needs Review."
- Lock indicator is prominent and unambiguous.

### Rollout Plan

1. **Phase 1** — Read-only dashboard: staging states, last edited, customer drill-down. No locking.
2. **Phase 2** — Edit presence indicator (live "being edited by").
3. **Phase 3** — Locking mechanism + force-release.
4. **Phase 4** — Policy metadata + "Needs Review" integration.

### Success Metrics

- Reduction in Slack/Linear threads asking "what is the current state of X criteria."
- Time for ESE to answer "what criteria does Customer X have deployed" (before vs. after).
- Zero concurrent-edit collisions after locking is live.

---

# 19. PRD: Stable Version History & Human-Readable Diffs
**Area:** Source of Truth | **Priority:** P0 | **Status:** Drafted

> **Goal:** Provide a full, stable version history for every order type, code, and service line — with editor, timestamp, and human-readable diff — so anyone can see exactly what changed, when, and who changed it.

### Background

The absence of reliable version history is one of the most frequently surfaced operational problems in the Qual system. The Nunns situation, as described by Ian Kennedy in #sku-qualifications-worker (March 2026), is the canonical example: Nunn's criteria drifted to V2 while the library is at V14, and the team had no way to see what changed between versions, which changes were Tennr-standard updates vs. custom edits, or which version was safe to pull forward.

Katherine Pelton announced versioning improvements in October 2025 (order type versioning with an audit log). The ask here is to extend that to a stable, human-readable diff view — not just a log, but a diff that tells you *what specifically changed* in terms a non-engineer can read and act on.

### Problem Statement

Version history exists in partial form but does not provide human-readable diffs. Teams cannot reliably compare criteria versions, understand what changed, or safely merge custom changes with new library versions.

### Goals

- Full version history for every order type, code, and service line.
- Each version entry: editor identity, timestamp, change summary.
- Human-readable diff: shows what text was added, removed, or modified in criteria — not just metadata changes.
- Diff is actionable: ESEs and writers can compare the current custom version to the latest library version and decide what to pull in.

### Non-Goals

- Automated merging of custom and library versions (human decision required).
- Version history for non-criteria fields (e.g., payer mapping config).

### Users

- **ESE teams** — need to reconcile a customer's custom criteria with a newer library version.
- **COE / criteria writers** — need to see what changed between their edits and an earlier version.
- **Ian Kennedy / implementation team** — specifically asked for a diff checker in #sku-qualifications-worker for Nunns and future similar cases.

### Proposed Solution

**Version History Panel**

Every order type, code, and service line has a "Version History" panel showing:
- Version number.
- Editor name.
- Timestamp.
- Change summary (auto-generated: "Added 2 criteria, modified 1, removed 0").

**Human-Readable Diff View**

Selecting any two versions shows a side-by-side diff:
- Added criteria: highlighted green.
- Removed criteria: highlighted red.
- Modified criteria: shows before/after text inline.
- Unchanged criteria: shown for context.

**Three-Way Diff (Custom vs. Library vs. Latest)**

For order types that are custom (diverged from the library), the diff view supports a three-way comparison:
1. Current custom version.
2. The library version the custom was based on.
3. The current library version (latest).

This allows ESEs to identify: which changes are custom additions, which are outdated library criteria, and what the latest library version offers.

### Requirements

**Functional**
- Version history panel on every order type, code, and service line.
- Human-readable diff between any two versions.
- Three-way diff for custom order types.
- Diff is read-only (acting on it is handled by bulk edit / clone tools).

**UX**
- Diff is readable by non-engineers (plain language, not technical patch format).
- Three-way diff clearly labels which column is which.

### Rollout Plan

1. **Phase 1** — Version history panel with editor + timestamp + change summary.
2. **Phase 2** — Human-readable two-version diff.
3. **Phase 3** — Three-way diff for custom vs. library comparison.

### Success Metrics

- Reduction in time for an ESE to reconcile a customer's custom criteria with the current library version.
- Reduction in incidents of unintended criteria overwrites during re-cloning.
- ESE and COE satisfaction with diff readability (qualitative).

---

# 20. PRD: Custom vs. Source Tracking for All Order Types
**Area:** Source of Truth | **Priority:** P1 | **Status:** Drafted

> **Goal:** Explicitly mark every order type as either Tennr-standard (cloned from QualHub) or custom, so teams always know which version of an order type they're looking at and what it was originally cloned from.

### Background

There is currently no reliable, system-enforced distinction between a Tennr-standard order type (cloned from QualHub, unmodified) and a custom order type (one where the criteria or config has been modified from the original clone). Teams rely on naming conventions and institutional memory — neither of which is reliable.

Jasper confirmed in #sku-qualifications-worker (March 2026) that this is being addressed in Versioning pt 2 as a lineage/attribute ("Tennr standard vs. custom"). The QUA-1377 Linear ticket tracks the attribute addition. This PRD formalizes the product requirements for that feature.

### Problem Statement

There is no reliable system-enforced indicator of whether an order type is Tennr-standard or has been customized. Teams cannot safely re-clone or bulk-update without risking overwriting legitimate customizations.

### Goals

- Every order type is explicitly marked as: **Tennr Standard** (cloned, unmodified) or **Custom** (modified from clone or created from scratch).
- The first modification to a cloned order type automatically changes its status to Custom.
- Custom order types show their original source (which QualHub order type they were cloned from).
- Archiving a custom order type requires a confirmation/blocker step (preventing accidental deletion of custom work).
- The standard/custom distinction is visible in all order type views, including the Criteria Dashboard.

### Non-Goals

- Auto-reverting custom order types to Tennr Standard.
- Merging custom and standard versions (handled by Version History diff feature).

### Users

- **ESE teams** — need to know before re-cloning whether a customer's order type has customizations worth preserving.
- **COE** — needs to see the distribution of standard vs. custom across the library.
- **Jasper / engineering** — building the lineage tracking as part of Versioning pt 2.

### Proposed Solution

**Status Attribute**

Each order type carries a `lineage_status` field:
- `tennr_standard` — cloned from QualHub, no modifications made.
- `custom` — one or more modifications have been made since cloning, or created from scratch.

**Auto-Transition**

The first edit to a cloned order type automatically transitions status from `tennr_standard` to `custom`. A confirmation modal informs the writer: "This will mark the order type as custom. You will need to manage updates manually going forward."

**Source Reference**

Custom order types retain a reference to the original QualHub source they were cloned from, including the version at time of cloning.

**Archive Blocker**

Attempting to archive a `custom` order type triggers a confirmation step: "This order type has been customized. Archiving it cannot be undone. Confirm?"

**Visibility**

- Standard/custom badge visible on order type cards in all views.
- Filterable in the order type browser.
- Shown in Criteria Dashboard drill-down.

### Rollout Plan

1. **Phase 1** — `lineage_status` attribute added to schema. Auto-transition on first edit. Source reference stored.
2. **Phase 2** — Badge visible in UI. Archive blocker for custom order types.
3. **Phase 3** — Filter in order type browser + Criteria Dashboard integration.

### Success Metrics

- % of order types with accurate lineage_status within 30 days of launch.
- Reduction in incidents of custom criteria being overwritten by re-cloning.
- ESE confidence in re-cloning decisions (qualitative).

---

# 21. PRD: Customer Toggle with Audit Trail
**Area:** Source of Truth | **Priority:** P1 | **Status:** Drafted

> **Goal:** Allow customers (or COE/ESE on their behalf) to toggle their own criteria on or off, with a required confirmation step and a visible audit trail entry for every toggle action.

### Background

Customers sometimes need to temporarily disable a criterion — for example, during a transition period, while a criteria update is being reviewed, or when a specific payer policy is under dispute. Today, toggling criteria on or off is an engineering-mediated action with no customer-visible audit trail.

Bruna linked this feature directly to the Nunns customer escalation in March 2026 and has a Notion spec page for it (Customer toggle with audit trail). The feature is also relevant to customer trust: if a criterion is toggled off, customers need to see that it happened, when, and by whom — otherwise they can't explain why Qual is or isn't checking a specific requirement.

### Problem Statement

Criteria can be toggled on or off, but this action has no customer-visible audit trail and requires engineering mediation. Customers cannot understand why their qual behavior changed after a toggle.

### Goals

- Authorized users (ESE or customer-role) can toggle a criterion on or off per customer org.
- Toggle requires a confirmation step (no accidental toggles).
- Every toggle action creates a visible audit trail entry: who toggled, what they toggled, when, and in which direction (on → off or off → on).
- Toggle state and audit trail are visible in the Criteria Dashboard.

### Non-Goals

- Auto-toggling criteria based on policy updates (human action only).
- Customer self-service toggle without ESE approval (v2 with a request/approval workflow).

### Users

- **ESE teams** — need to toggle criteria for customers as part of implementation and maintenance.
- **Customers** — need to see the toggle history for their criteria to understand qual behavior changes.
- **COE** — needs audit visibility across all toggle events.

### Proposed Solution

**Toggle Control**

In the order type view within a customer org, each criterion has an active/inactive toggle. Toggle is available to authorized roles (ESE, COE, admin).

**Confirmation Step**

Toggling a criterion (either direction) triggers a confirmation modal:
- "You are about to [enable / disable] [criterion label] for [customer name]. This will [take effect immediately / take effect on next Qual run]. Confirm?"
- Optional free-text reason field (logged).

**Audit Trail Entry**

Every confirmed toggle creates an audit entry:
- Criterion label.
- Previous state + new state.
- Actor (who toggled).
- Timestamp.
- Reason (if provided).

Audit trail is visible in:
- The criterion's detail view.
- The Criteria Dashboard.
- Exportable as a report per customer.

### Requirements

**Functional**
- Toggle control on each criterion within a customer org order type.
- Confirmation modal required for every toggle.
- Audit trail entry created for every confirmed toggle.
- Audit trail visible in criterion detail and Criteria Dashboard.

**UX**
- Toggle state is visually unambiguous (active/inactive clearly indicated).
- Confirmation modal clearly states the impact.
- Audit trail is sortable and filterable.

### Rollout Plan

1. **Phase 1** — Toggle control + confirmation modal. Audit trail entry created.
2. **Phase 2** — Audit trail visible in Criteria Dashboard.
3. **Phase 3** — Customer-visible audit trail export.

### Success Metrics

- Zero unintentional criteria toggles after confirmation modal launch.
- ESE time to toggle a criterion and explain the change to a customer (before vs. after).
- Customer-reported clarity on why Qual behavior changed after a toggle.

---

# 22. PRD: Flag When Order Type Is Out of Date from Its Parent
**Area:** Source of Truth | **Priority:** P1 | **Status:** Drafted

> **Goal:** When a parent order type or service line is updated in QualHub, automatically flag any cloned children that have diverged as "out of date," showing what changed upstream and letting ESEs choose to pull in the update or dismiss.

### Background

The Nunns escalation is the canonical example: Nunn's order types were at V2 while the library was at V14 — a 12-version gap that no one detected until a customer escalation. The automated "Outdated Order Types Notice" bot already fires when order types fall behind (visible in #ops-tennr-criteria-management), but it provides a Linear ticket, not a visual indicator in the UI. ESEs must act on the ticket, find the order type, compare manually, and decide what to do.

Jasper's message in #sku-qualifications-worker (March 2026) confirms engineering is building lineage tracking (QUA-1377) as part of Versioning pt 2. This PRD defines the product behavior that sits on top of that lineage.

### Problem Statement

Cloned order types that fall behind their QualHub parent are not surfaced visually in the product. ESEs discover drift only via manual review or when a customer escalates a criteria accuracy issue.

### Goals

- When a parent order type or service line is updated in QualHub, any cloned children are automatically flagged as "out of date."
- The flag shows: what changed upstream (linked to version diff), how many versions behind.
- ESE can: pull in the update (with preview), or dismiss the flag (with reason + audit entry).
- Flag is visible in the Criteria Dashboard and in the order type card itself.

### Non-Goals

- Auto-applying the parent update without ESE review.
- Flagging custom order types that intentionally diverge (custom status is respected).

### Users

- **ESE teams** — need to proactively know when a customer's order types are behind and decide whether to update.
- **COE / criteria writers** — need visibility into which customer orgs are running on outdated versions.
- **Ian Kennedy / implementation teams** — specifically requested this capability for Nunns-type situations.

### Proposed Solution

**Out-of-Date Detection**

When a QualHub order type or service line is updated (new version deployed), the system:
1. Identifies all cloned children across all customer orgs.
2. For each child: compares the child's last-synced version to the new parent version.
3. If diverged (child version < new parent version): marks child as `out_of_date`.

**Visual Indicator**

Out-of-date order types display a badge: "⚠ Out of date — parent updated [date]."
- Badge visible on order type cards in customer org view and Criteria Dashboard.
- Clicking the badge shows: what changed in the parent (linked to version diff), versions behind count.

**ESE Actions**

From the out-of-date indicator, ESEs can:
1. **Pull in update** — opens a diff preview of what would change in the child. Requires confirmation. After confirmation, child criteria are updated and `out_of_date` flag clears.
2. **Dismiss** — clears the flag for this version increment. Requires a reason. Logged in audit trail. Re-fires if a newer parent version is released.

### Requirements

**Functional**
- Automated detection when cloned children fall behind their parent version.
- Out-of-date flag with version diff context.
- Pull-in-update flow with diff preview + confirmation.
- Dismiss flow with reason + audit log.
- Flag respects custom status (custom order types can be flagged but ESE has full discretion).

**UX**
- Badge is visually distinct and actionable from the order type card.
- Pull-in-update preview clearly shows what will change before confirming.
- Dismissed flags do not resurface for the same version (only for newer updates).

### Rollout Plan

1. **Phase 1** — Out-of-date detection + flag. No pull-in-update yet. ESEs act via existing re-clone flow.
2. **Phase 2** — Pull-in-update flow with diff preview.
3. **Phase 3** — Dismiss with reason + audit trail. Integration with Criteria Dashboard.

### Success Metrics

- Reduction in version-behind gap at time of detection (from current ~12 versions in worst case to flagged within 1 version).
- Time for ESE to act on an out-of-date flag (pull in or dismiss) after being notified.
- Reduction in customer escalations caused by criteria version drift.
