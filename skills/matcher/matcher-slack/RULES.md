# Matcher Shared Rules

This is not a triggerable skill on its own — it's the shared logic every `matcher-*` skill reads first, so classification rules stay consistent no matter which source triggered a run. If you're in a source-specific matcher skill, read this file in full before doing anything else.

## Core IDs (don't re-derive these — use them directly)

| Database | data_source_id | database url |
|---|---|---|
| Projects DB | `49abc962-2180-419d-a398-2a4a6aec0330` | `e0dd6b8b8cae400e9d1861350dcd8112` |
| Commitments DB | `9335dd08-21de-482a-bd35-8b040f1d24f2` | `4c1b6e5ac3054d67954fb3665fd15fa0` |
| People Directory | `ae695dac-2bd0-4b7b-94bf-6ff710d8d3c5` | `21fa593b1e6e43a6bc18a33cda97bd84` |
| Meeting Notes | `1b4eb680-c7fc-802d-94f6-000b412c3dd0` | `1b4eb680c7fc806096f5d9d903ed5998` |
| Tennr Today | `d0c67898-a20f-4bff-8f8d-163c19b8a51e` | `b1866b186fd648ffa32bde942bb4a2a1` |
| Meeting Agendas | `1bf1ffde-493c-4666-983b-8e98d35094a5` | `3d119a1592184725888105d9bd0555b3` |

Never auto-creates a new "real" Projects DB row and never auto-executes a delegation. Both require Bruna's confirmation — this is a hard rule, not a preference.

## Category / Project / Thread / Task

Every Projects DB row has an `Item Type`: **Category** (durable — a customer/account like "J&B," or an initiative like "Criteria Factory"), **Project** (discrete work with a defined outcome), **Thread** (ongoing conversational context spanning multiple touchpoints over time), or **Task** (a single, closable action).

**The real test for "does this account deserve its own Category":** is the activity fundamentally *criteria writing/maintenance*, or is it broader account complexity — implementation/onboarding, product rollout decisions, escalations, roadmap conversations, churn risk? J&B and Comfort Medical earned Categories because of order-creation platform work, onboarding, and roadmap conversations — not just criteria tickets. Volume of tickets alone does not justify a Category — nature of the work does.

**Prospects never get their own Category, no matter how active the deal is** — every prospect nests as a `Project` under the single **Sales/Prospects** Category (`39feb680-c7fc-81ae-9ae5-e80f7ec0d7cb`), tagged via `Customer`. Promote to a real Category only once they convert to a paying customer.

A customer with only a single one-off ticket also doesn't get its own Category — nest it under a workstream Category (e.g. **Criteria Updates**, `39feb680-c7fc-81e2-a65d-c1e4be45987c`) with `Customer` set on that row. When in doubt, default to nesting — easy to promote later, hard to un-sprawl.

**Capture every one-off item — never let one die silently — but type it correctly:**
- Single action that closes out, won't recur → **Task**.
- Part of an ongoing situation with multiple future touchpoints → **Thread**.
- When unsure, default to **Task** — Tasks are meant to be numerous and short-lived; Threads should stay a small set of genuinely persistent situations.

A completed Task or Thread is marked `Status = Done`, never deleted — stays for audit history, just drops off the "Do First" dashboard view.

Default new unmatched items to Task or Thread, nested under a Category via the native **Parent item** field (Notion's built-in Sub-items — not a custom field). Never default something to Category — Categories are created deliberately. If no Category exists yet for an obvious customer/initiative, create it first, then set the new item's Parent item to point to it.

## Matching logic

For each raw item, extract: the customer/account name if any, distinctive proper nouns, and the source link. Query Projects DB for rows whose Project Name, Customer, or Source Refs share those terms.

- **Strong match**: tag directly — append the link to `Source Refs`, touch `Last Updated`.
- **Weak/no match**: do NOT create a new "real" row. Create/add to a Review Queue entry (`Status = Idea/Unstaged`, `Needs Review = true`).
- **Multiple plausible matches**: don't guess — Review Queue with the candidates named.

Never merge two rows automatically, even if they look like duplicates — flag the possible duplicate instead.

Once an item has a confirmed home, clear `Needs Review`. Stale review flags are as bad as missing ones.

## Response Status — set on every item from every source

`Response Status` (`Needs Response` / `FYI` / `Ambiguous`) is set on **every** item, no exceptions. Source-specific mapping rules live in each source skill (e.g. how the Response Triage canvas's own five-way classification maps onto this field) — but the field itself is universal, never source-specific.

## Every "Needs Response" item is also a commitment

Any row tagged `Response Status: Needs Response` is, by definition, an obligation Bruna owes someone. **Automatically create a matching Commitments DB row** (`Direction: Owed by Me`, `Loop Type: Commitment`) linked via the `Project` relation — unless one already exists for that item (check by `Project` relation first, never duplicate). Applies regardless of size — a five-minute reply and a multi-day deliverable both get a row; size is tracked via time estimate, not by which database it lives in. Commitments DB is the complete ledger in both directions; Projects DB is the account/hierarchy view of the work. Two databases, cross-linked, never merged.

**Every new row in either database — Commitments or Projects — must have `Time Estimate` set at creation, no exceptions.** Quick (<15min) for a reply/confirmation, Short (15-30min) for a standard response or small review, Medium (30-60min) for real analysis/writing, Deep (60min+) for a multi-step deliverable. If genuinely unsure, default to Short rather than leaving it blank — an unset Time Estimate silently breaks the calendar-matching feature downstream. This has been a real, recurring gap — check it explicitly before finishing any create-page call, don't treat it as optional metadata.

Also set `Project` (linking back to the relevant Projects DB row) whenever one exists, and `Owed To` (who the counterparty is) whenever it's identifiable from the source — both have been silently skipped in past runs and shouldn't be treated as optional either.

## Delegation recommendation

| Trigger pattern | Recommend |
|---|---|
| Criteria writing/content — QA judgment on existing criteria | Stacey |
| Criteria writing/content — customer-facing framing/scope | Tess |
| Criteria writing/content — strategic/precedent-setting or cross-vertical | Bruna |
| Customer feedback | Tess |
| Ticket/intake/project status, customer-facing scope or timeline | Mary |
| Analysis / capacity modeling | Sean |
| Anything else strategic, exec-facing, or ambiguous | Bruna |

Write to `Recommended Delegate`. Leave `Delegation Confirmed` unchecked — that's Bruna's checkbox. Never message, reassign, or notify based on a recommendation until she confirms it.

## Aging / escalation

| Priority | Escalates after | Fades after |
|---|---|---|
| P0 | 2 days untouched | never fades |
| P1 | 5 days | 14 days |
| P2 | 10 days | 21 days |
| P3 | — | 14 days |

`Days Since Update` and `Super Past Due` are real formula fields on Projects DB — don't recompute manually, query them directly.

## Write results, then report

- Tag matches: update `Source Refs` and `Last Updated`.
- Unmatched/ambiguous: Review Queue (`Needs Review = true`).
- Delegation: attach recommendation, never execute.
- After a run: short summary — how many matched, how many to Review Queue and why, delegation recommendations awaiting confirmation. Don't dump the raw item list; Bruna reviews specifics in the live views.

## What matcher skills deliberately do NOT do

- Auto-create "real" (non-review-queue) Projects DB rows
- Send messages, reassign Linear tickets, or notify people
- Merge or delete Projects DB rows
- Fabricate wins, priorities, or context not actually found in a source — if nothing turned up, say so
