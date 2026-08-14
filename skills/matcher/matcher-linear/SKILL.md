---
name: matcher-linear
description: Pulls Linear issues assigned to or mentioning Bruna and tags them into the Projects DB per the shared matcher rules. Use whenever Bruna says "check Linear," "sync Linear to projects," "run the Linear matcher," or "what's overdue in Linear." Always read RULES.md (bundled in this skill folder) first.
---

# Matcher: Linear

Read `RULES.md (bundled in this skill folder)` in full before doing anything below.

## Gathering

`Linear:list_issues` with `assignee: "Bruna"`. Filter out `status: "Done"` / `statusType: "completed"` — only unstarted/in-progress issues matter.

**Tool note:** this failed repeatedly across an entire earlier session before working on retry with no configuration change. Don't assume it's broken without a fresh attempt — retry 2-3 times before concluding it's actually down and reporting that to Bruna.

## What to watch for

`slaBreachesAt` dates in the past on still-open issues are consistently the highest-signal find — two J&B SLA-breached-since-7/1 tickets and a 6-month-overdue Ken Glover ticket all surfaced immediately on first real use. Always check for this specifically, don't just list issues in whatever order the API returns them.

## Matching

Linear issues are usually customer-specific (the customer name is often in the issue title or description) — match against Projects DB `Customer` field first before falling back to keyword matching on the title.
