---
name: matcher-meetings
description: Crawls Bruna's Notion Meeting Notes DB for unprocessed content and tags it into the Projects DB per the shared matcher rules. Use whenever Bruna says "check meeting notes," "sync meeting notes to projects," "crawl my meetings," or "did I miss anything from meetings this week." Always read RULES.md (bundled in this skill folder) first.
---

# Matcher: Meeting Notes

Read `RULES.md (bundled in this skill folder)` in full before doing anything below.

## Critical: the real content is in the page body, not the properties

The Summary/Wrap Up database properties are frequently null even for meetings with substantial real content. **The actual notes live inside a `<meeting-notes>` block in the page body itself** (a Granola-style transcription integration), containing a `<summary>` with real Action Items and topic-by-topic breakdowns. Always `notion-fetch` the actual page and read its body content — never conclude a meeting has "no notes" based on empty properties alone. This was a real mistake made once already; don't repeat it.

## Finding recent meetings

Use `Created time`, not `Meeting Date` — that field is populated on under 10% of rows and is unreliable for filtering.

## Customer Name inference

Meeting Notes has a `Customer Name` multi-select, but Bruna does not fill it out herself. Infer and set it during each run from meeting title, attendees, and page content. Treat an empty field as "not yet inferred," not "no customer." Once inferred, it's the primary match signal against Projects DB `Customer`.

## Linking

Every processed meeting note gets a `Related Project` relation pointing to the Projects DB row(s) it touches — this is what makes the Meeting Note → Meeting Agendas → Projects chain work. A single meeting can surface multiple distinct action items across several accounts (a dense 1:1 or onsite debrief often does) — each gets its own Task/Thread, not one row trying to cover everything.

## Report

Note explicitly which meetings had real content vs. which were genuinely empty placeholders — don't imply full coverage if several were empty. If a run finds a pattern of empty notes (meetings happening with nothing written up afterward), flag that as a process gap, not a matcher failure — more crawling doesn't fix a note that was never written.
