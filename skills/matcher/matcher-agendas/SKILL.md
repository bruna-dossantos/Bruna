---
name: matcher-agendas
description: Builds Bruna's daily meeting agendas by synthesizing the Meeting Prep canvas together with full context from Projects DB, Commitments DB, Meeting Notes DB, and People Directory (for 1:1s only) — not just condensing the canvas in isolation. Use whenever Bruna says "build today's agendas," "prep my meetings," "what do I need for today's meetings," or as the first step of a morning routine before checking messages. Always read RULES.md (bundled in this skill folder) first.
---

# Matcher: Meeting Agendas

Read `RULES.md` (bundled in this skill folder) in full before doing anything below.

## IMPORTANT: canvas structure changed on 7/22

There is no longer a separate "Meeting Prep" canvas. As of 7/22, all Slack canvases were consolidated into one called **"Full Day Ready · [Month Day, Year]"**, and the per-meeting content now lives in that canvas's **"Today's Meetings"** section. Find it via file search: `Full Day Ready type:canvases`, most recent for today. Read the whole canvas, but only use the "Today's Meetings" section for this skill — the rest of the canvas (Do First, Response Triage, etc.) is handled by matcher-slack, not here, to avoid duplicate work on the same canvas.

## This is a synthesis job, not a condensing job

The canvas gives you the starting point for each meeting — but the actual agenda has to be built from everywhere relevant, not just that one source. For every meeting on today's calendar:

1. **Start with the "Today's Meetings" section** of the Full Day Ready canvas — each meeting entry has What to Know, Open Loops, Decisions/Questions to Raise, Suggested Talking Points, and sometimes Relevant Sources.
2. **Pull every currently-open Projects DB item tied to that meeting's account** — Active Threads/Tasks under the relevant Category (not just what the canvas happened to mention). This is what makes a J&B meeting show the overdue Medicaid tickets and Patient Hub decision even if the canvas itself didn't surface them that day.
3. **Pull open Commitments** tied to that account or attendees, both directions — anything owed by Bruna or to her that's relevant to who's in the room.
4. **Pull the most recent Meeting Notes DB entries** for that account, if any — prior context, unresolved action items from last time.
5. **If — and only if — the meeting `Type` is `1:1`**: also pull that person's People Directory page (Notes, Priorities/Goals, Wins, Projects/Things to Discuss). Do not do this for group, customer, or internal multi-person meetings — full person-history context is a 1:1-only feature, this was decided explicitly and should not creep into other meeting types.

## Writing the result

Same as before: write one row per meeting into the Meeting Agendas DB, never a freeform page. `Agenda` = 3-5 concrete numbered bullets synthesized from all of the above, not just restated from the canvas. If context from Projects DB/Commitments contradicts or extends what the canvas said (e.g. the canvas doesn't mention an item that's actually overdue), the agenda should reflect the fuller picture — the canvas is a starting point, not a ceiling.

Datetime, Stakes, Type, Attendees, Related Project, Meeting Note fields — same rules as before (see RULES.md).

## Sequencing matters

This skill should run **after** the messaging sources are checked (matcher-slack, matcher-linear, matcher-meetings, matcher-chat), not before — agendas built on stale context defeat the point. If invoked as part of a morning routine, it should be the last step, not the first, even though it's about the day ahead.

**This must run as five separate sequential steps, not one combined pass.** Complete each step fully — including writing its results to Notion — before starting the next. Do not run them in parallel and do not treat this as "gather everything, then process." The order exists specifically so each later step sees the results the earlier ones already wrote:

1. Run matcher-slack completely. Confirm it finished (items tagged, Response Status set) before moving on.
2. Run matcher-meetings completely.
3. Run matcher-linear completely.
4. Run matcher-chat completely.
5. Only now run matcher-agendas — it depends on Projects DB, Commitments DB, and Meeting Notes already reflecting everything from steps 1-4. Running it earlier means it builds agendas from stale data, which defeats the entire point of this skill.

Report progress step by step, not as one silent block — e.g. "Step 1/5: Slack sync complete, 8 items tagged" — so a partial failure is visible rather than discovered later.
