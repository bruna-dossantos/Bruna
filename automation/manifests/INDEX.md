# Automation Manifests — Index

Generated from Bruna's scheduled-task wrapper skills. Each wrapper is a thin schedule
pointing at a real (canonical) skill. Sources were read-only; nothing under
`~/Documents/Claude/Scheduled/` or `~/.claude/scheduled-tasks/` was modified.

| wrapper | schedule | canonical skill | notes |
|---------|----------|-----------------|-------|
| 11-prep | UNKNOWN — confirm (weekly implied) | one-on-one-prep | "for all 1 on 1 meetings this week"; body is `/one-on-one-prep` |
| daily-brief | UNKNOWN — confirm (daily, morning) | daily-briefing | only daily job; no time-of-day duplicate |
| follow-up-sundays | UNKNOWN — confirm (weekly, Sunday) | follow-up-tracker | pairs with follow-up-wednesday |
| follow-up-wednesday | UNKNOWN — confirm (weekly, Wednesday) | follow-up-tracker | pairs with follow-up-sundays |
| meeting-notes-review | UNKNOWN — confirm | meeting-notes-review | base time-of-day variant |
| meeting-notes-review-afternoon | UNKNOWN — confirm (afternoon) | meeting-notes-review | afternoon variant |
| meeting-notes-review-night | UNKNOWN — confirm (night) | meeting-notes-review | night variant |
| one-on-one-prep | UNKNOWN — confirm | one-on-one-prep | body is "Run one-on-one-prep skill" |
| slack-triage | UNKNOWN — confirm | slack-reply-triage | base variant; canonical = slack-reply-triage |
| slack-triage-afternoon | UNKNOWN — confirm (afternoon) | slack-reply-triage | afternoon variant |
| team-pulse | UNKNOWN — confirm (weekly) | team-pulse | no time-of-day duplicate |
| weekly-one-on-one-prep | UNKNOWN — confirm (weekly, next 7 days) | one-on-one-prep | fully-specified; lives in `~/.claude/scheduled-tasks/`, not `Scheduled/` |

## Duplicate / consolidation candidates

Several wrappers invoke the SAME canonical skill at different times of day (or with no
stated time at all). These should collapse to one canonical skill + a time-of-day / day
parameter rather than being recreated as separate schedulers.

- **meeting-notes-review** ← collapses 3 wrappers into `meeting-notes-review` with a `time-of-day` parameter:
  - `meeting-notes-review` (base)
  - `meeting-notes-review-afternoon` (afternoon)
  - `meeting-notes-review-night` (night)
  → One skill, runs up to 3x/day. Confirm whether 3 daily runs is intended or leftover experimentation.

- **slack-reply-triage** ← collapses 2 wrappers into `slack-reply-triage` with a `time-of-day` parameter:
  - `slack-triage` (base)
  - `slack-triage-afternoon` (afternoon)
  → One skill, runs 2x/day (morning + afternoon). Note the wrappers are named "slack-triage" but the canonical skill is `slack-reply-triage`.

- **follow-up-tracker** ← collapses 2 wrappers into `follow-up-tracker` with a `day` parameter:
  - `follow-up-sundays` (Sunday)
  - `follow-up-wednesday` (Wednesday)
  → One skill, runs 2x/week (Sun + Wed).

- **one-on-one-prep (1:1 prep)** ← LIKELY collapses 3 wrappers into a single 1:1-prep automation:
  - `~/Documents/Claude/Scheduled/11-prep` (body `/one-on-one-prep`, "all 1:1s this week")
  - `~/Documents/Claude/Scheduled/one-on-one-prep` (body "Run one-on-one-prep skill")
  - `~/.claude/scheduled-tasks/weekly-one-on-one-prep` (fully-specified weekly, next 7 days)
  → These three MAY all be the same 1:1-prep automation, created at different times / places. `weekly-one-on-one-prep` is the fully-fleshed-out version (embedded Steps 1–5, key Notion IDs, Known People table) and should be treated as the canonical config; `11-prep` and `one-on-one-prep` look like earlier/duplicate stubs. Confirm with Bruna before deleting either stub.

Skills with NO duplicate (one wrapper each): `daily-brief` → daily-briefing, `team-pulse` → team-pulse.

## Before recreating any of these as real schedulers

- **Check Akiflow / the existing scheduler first.** Per Bruna's standing rule ("always check
  Akiflow before creating duplicates"), verify no equivalent recurring task already exists
  before registering any of these — otherwise the same skill could fire twice.
- **All schedules are UNKNOWN.** No wrapper states an actual cron/time/day; times of day are
  inferred only from names/descriptions. Confirm the intended cadence for every automation
  before scheduling.
- **Consolidate before scheduling.** Register the collapsed canonical-skill + parameter form
  above, not the individual wrappers, to avoid duplicate recurring tasks.
