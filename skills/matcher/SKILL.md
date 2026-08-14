---
name: project-matcher
description: Full-sweep orchestrator for Bruna's operating infrastructure — invokes all five source-specific matchers (Slack, Meeting Notes, Linear, Chat, Agendas) in sequence, then gives one consolidated summary. Use whenever Bruna says "run the matcher," "sync everything," "full sweep," "catch me up on everything," or "tag everything to projects." For a single source only, invoke the specific matcher-slack / matcher-meetings / matcher-linear / matcher-chat skill instead — this orchestrator is for when she wants all of them run together.
---

# Project Matcher — Full Sweep

This skill contains no classification logic itself — each of the four source skills (matcher-slack, matcher-meetings, matcher-linear, matcher-chat) carries its own bundled copy of the shared rules (RULES.md) and applies them consistently.

## Run order

When this skill is invoked, work through each source in turn, applying the same skill-invocation behavior you'd use if Bruna had asked for each one individually:

1. matcher-slack — Daily Briefing, Response Triage, Meeting Prep canvases, plus the Notion notifications channel.
2. matcher-meetings — Meeting Notes DB.
3. matcher-linear — Linear issues.
4. matcher-chat — recent chat history.
5. matcher-agendas — LAST, after the above, so agendas reflect fresh context, not stale canvases.

## Why split by source at all

Each source has a genuinely different rhythm and failure mode: Slack canvases refresh multiple times a day and need frequent checks; meeting notes only matter right after a meeting happens; Linear moves slower and has had real tool reliability issues; chat capture is opportunistic. Forcing all four into one giant procedure risked steps getting silently skipped on a long run, and made it impossible to run just one source without dragging the others along. The shared rules bundled into each one prevent the real risk of splitting — two sources disagreeing about what counts as urgent, or duplicating the same commitment from two different angles.

## Reporting

Don't give four separate summaries. Collect results from all four passes, then give Bruna **one** consolidated summary at the end: total items matched, total routed to Review Queue (grouped, with why), any new Categories created, delegation recommendations awaiting confirmation, and anything that looked genuinely urgent across any source. She reviews specifics in the live Notion views, not by reading a wall of chat text.
