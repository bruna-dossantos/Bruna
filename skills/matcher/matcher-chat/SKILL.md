---
name: matcher-chat
description: Scans Bruna's recent Claude chat history for new project/idea signals and stale unresolved threads, tagging findings into the Projects DB per the shared matcher rules. Use whenever Bruna says "check my chats," "capture ideas from chat," "run chat self-capture," or "did I forget something from a conversation." Always read RULES.md (bundled in this skill folder) first.
---

# Matcher: Chat Self-Capture

Read `RULES.md (bundled in this skill folder)` in full before doing anything below.

## Scope limitation — say this out loud if relevant

Claude-only. This cannot see ChatGPT or any other tool's conversation history. If Bruna's asking about something she thinks she discussed elsewhere, say so rather than silently returning nothing.

## Procedure

1. Call `recent_chats` for the last 24-48 hours, or since the last run if known.
2. For each conversation, scan for:
   - **New project/idea signal** — Bruna proposing to build something, naming a new initiative, or a new customer/prospect mentioned for the first time.
   - **Stale/abandoned signal** — a conversation that ended mid-task without clear resolution or handoff.
3. **New idea** → create a Task or Thread (per shared rules) with `Origin = Chat`, `Origin Link` to the conversation, `Status = Idea/Unstaged`, `Needs Review = true` unless it clearly matches an existing Category.
4. **Stale chat** → don't create a row for the chat itself. Check if its topic already has a home in Projects DB — if yes, note "last discussed in chat, unresolved" in that row's Next Step. If no, log to Review Queue as a Task noting it needs Bruna to decide if it's still relevant.
5. Report a short count only ("found N new ideas, M stale threads") — don't dump chat contents into the summary.
