---
name: matcher-slack
description: Reads Bruna's single unified "Full Day Ready" Slack canvas (which now contains Do First, What Changed, Response Triage, Next 3 Business Days, and Recommended Actions all in one document), plus her Notion-notifications-in-Slack channel, and tags items into the Projects DB and Commitments DB per the shared matcher rules. Use whenever Bruna says "check today's canvas," "run the Slack matcher," "sync Slack to projects," or "check my Notion notifications." For meeting agendas specifically, use the separate matcher-agendas skill instead — it reads the "Today's Meetings" section of this same canvas but synthesizes additional context (Projects DB, Commitments, Meeting Notes, People Directory) on top of it. Always read RULES.md (bundled in this skill folder) first.
---

# Matcher: Slack (messaging sources)

Read `RULES.md` (bundled in this skill folder) in full before doing anything below — this skill assumes those rules and doesn't repeat them.

## IMPORTANT: canvas structure changed on 7/22

Prior to 7/22, there were three separate canvases (Daily Briefing, Slack Response Triage, Meeting Prep). **As of 7/22 these were consolidated into a single canvas called "Full Day Ready · [Month Day, Year]"** containing all of their content in one document. Do not search for the old three titles — they no longer exist. If this changes again in the future, re-verify by actually reading a canvas rather than assuming the old structure still applies — this skill has already been wrong about canvas structure once.

## Finding today's canvas

Find via file search: `slack_search_public_and_private` with `content_types="files"` and query `Full Day Ready type:canvases`, `sort="timestamp"`. This surfaces canvas file objects with File ID and creation time — general message search does not. If multiple canvases share today's date, use the most recently created one. Read via `slack_read_canvas` using the File ID.

## Sections within the canvas, and what to do with each

- **Do First**: the day's top action items, often with an "Unlock of the day" framing. → `Response Status: Needs Response`, high priority.
- **What Changed**: informational/status updates. → `Response Status: FYI`.
- **Response Triage**: has its own four-bucket classification with a summary count. Map directly: `Needs Response` and any unresolved bucket with a red/yellow indicator → `Response Status: Needs Response`. `Responded/Likely Resolved` and `Resolved by Others` → `Response Status: FYI` (set `Status: Done` if fully closed). `Follow-Up Pending` → belongs in Commitments DB (Owed to Me), not as a Response Status here — same rule as before. The canvas also includes **Suggested Replies** for some items — these are drafts Bruna can use, not something to act on autonomously.
- **Today's Meetings**: this section now lives in the same canvas but is handled by the **matcher-agendas** skill, not this one — don't process it here, to avoid duplicate/conflicting work.
- **Next 3 Business Days**: forward-looking deadlines and dependencies. Check each against Projects DB — if something here isn't already tracked, it becomes a new Task/Thread with an appropriately-set priority based on how soon it's due.
- **Recommended Actions**: lower-urgency items explicitly framed as "stay looped" or "no action needed today." → `Response Status: FYI` in most cases, but read the specific framing — some of these do need a nudge (e.g. "may need your nudge") and should be `Needs Response` at low priority instead.
- **Bottom line**: a synthesized summary — useful for your own run summary to Bruna, not a new source of items itself.

## Notion notifications channel (`D08HFT1AY3C`)

This is Bruna's Notion activity (page shares, comments, mentions) piped into Slack — the real "what's new in Notion that involves me" feed. Read via `slack_read_channel`, paginating with `cursor` since the last run.

Each message is: added to a page, commented on, or @mentioned. Extract page title, Notion URL, who did it, comment text.

**Classify every item:**
- **Needs Response/Action** — direct question, @mention asking something, expected to weigh in, added ahead of a deadline. → Priority reflects urgency, feeds "Do First."
- **FYI/Passive** — cc'd with no question, resolved thread, informational share. → Logged, low priority, doesn't clutter "Do First."
- **Ambiguous** — unclear if reply expected. → Review Queue.

A cluster of many comments on one page (someone doing a heavy review) is a signal — log as one high-priority Task summarizing the review, not one row per comment. Match to a Category the same way as any other source; Review Queue if none exists.

**Known-broken, don't use:** `notion-search` requires a non-empty query and returns noisy relevance-ranked results across all connected sources — it cannot browse purely by recency. The Slack channel above is the real mechanism.

## Supplementary Slack search

For freshness/verification only, after the canvas snapshot — targeted keyword searches, not broad sweeps.

## Report

Separate "needs your response" from "FYI only" explicitly in the summary — never one undifferentiated list.
