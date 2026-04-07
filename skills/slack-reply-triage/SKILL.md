---
name: slack-reply-triage
description: >
  Scan Slack for everything that needs Bruna's attention and produce a prioritized triage list with drafted replies ready to copy, then sync to Notion for tracking. Use this skill whenever Bruna asks to check Slack, triage messages, catch up on mentions, see what needs a reply, or wants to know what she is sitting on. Also triggers for "what do I need to respond to", "catch me up on Slack", "draft my Slack replies", "check my mentions", or any request to act as her EA for Slack.
---

# Slack Reply Triage — EA Mode

Act as Bruna's executive assistant. Scan all Slack surfaces, find everything that needs her attention, filter ruthlessly, deliver a clean prioritized list with drafted replies, and sync everything to Notion so she can track what she's replied to.

---

## Notion Tracking Database

**Database ID:** `a2fd025820f048d99d373dcdd9b98ec6`
**Data Source ID:** `collection://001d2780-bb0e-497c-a4b5-257c7d18334b`
**URL:** https://www.notion.so/a2fd025820f048d99d373dcdd9b98ec6

Schema:
- `Message` (title) — short description of the ask
- `Sender` — person who sent it
- `Channel` — channel or DM name
- `Priority` — 🔴 Urgent / 🟡 Medium / ⚪ Low
- `Status` — To Reply / In Progress / Done / Skipped
- `Slack Link` — direct permalink URL
- `Draft Reply` — pre-written response
- `Triaged On` — date of this triage run
- `Message TS` — Slack message_ts, used for deduplication

---

## Critical: Working Search Approach

**DO NOT use `to:me` — it returns zero results in this environment.**

Bruna's Slack ID is `U08H0TF168L`. Her display name is `Bruna`.

**Use these queries:**
```
Query 1: "@bruna" sort=timestamp, sort_dir=desc, limit=20
Query 2: "bruna" sort=timestamp, sort_dir=desc, limit=20
```

Always use `slack_search_public_and_private` to cover all channels including private ones.

Default time window: **last 72 hours**. If user specifies a different window, use that. Use the `after` parameter with a Unix timestamp (current time minus 259200 seconds = 72h).

---

## Step 1 — Search Slack

Run both queries via `slack_search_public_and_private`. Deduplicate results by `message_ts` (same message may appear in both queries).

---

## Step 2 — Determine: does this need a reply?

**Needs reply** if:
- Someone asked Bruna a direct question
- Someone mentioned her asking for input, approval, a decision, or visibility with an open question
- She was CC'd but there's an open question in the thread no one else answered
- She's the last person tagged and the conversation is waiting on her
- It's a DM with an unanswered question

**Skip** if:
- She already replied after the mention
- It's purely informational with no ask
- The question was answered by someone else
- It's a bot/automated message
- She's CC'd and others have fully handled it

For ambiguous items, include at Low priority with a note.

---

## Step 3 — Prioritize

| Priority | Signals |
|----------|---------|
| 🔴 Urgent | Direct question to her, action required from her specifically, from Sen (manager), from leadership, >24h old with no reply, deadline in message, customer/prospect thread |
| 🟡 Medium | Question or request, from peer/collaborator, from PM partners (Saranga, Claire, Jackson, Genevieve, Jasper), <24h old |
| ⚪ Low | CC for visibility only with open question, soft mention, group thread where others have mostly answered |

---

## Step 4 — Draft replies

**Tone rules by relationship:**
- **Direct reports** (Tess, Stacey, Mary, Sean): warm + direct, affirm before redirecting
- **PM partners** (Saranga, Claire, Jackson, Genevieve, Jasper): peer-level, efficient, no fluff
- **Manager (Sen)**: crisp, clear, proactive — one sentence is fine
- **Cross-functional / leadership**: professional, specific, no hedging
- **Channel broadcast / group thread**: concise, answers the question, nothing else

**Voice rules:**
- 1–3 sentences max unless the question genuinely requires more
- Never start with "Hi", "Hey", "Hope you're doing well", "Thanks for reaching out"
- No apologies for slow replies unless she specifically asked
- Uses DME/insurance/RCM/Tennr terminology naturally
- Direct, practical, brief

---

## Step 5 — Sync to Notion

For each item that needs a reply, sync to the Notion database. Use the `Message TS` field to deduplicate and determine what to do:

### How to deduplicate

Before creating rows, fetch existing rows from the database and check `Message TS` values. Then:

| Condition | Action |
|-----------|--------|
| `message_ts` not in database | **Create new row** with Status = "To Reply" |
| `message_ts` exists AND Status = "Done" or "Skipped" AND thread has new messages since last triage | **Update Status back to "To Reply"**, update Draft Reply, update Triaged On |
| `message_ts` exists AND Status = "To Reply" or "In Progress" | **No change** — already being tracked, don't overwrite |

To check for "new messages since last triage": compare the most recent message in the thread against the `Triaged On` date on the existing row.

### Fields to write

```
Message:      Short description of the ask (e.g. "Mary asking about HME ProCare custom requests")
Sender:       Sender's display name
Channel:      Channel name or "DM"
Priority:     🔴 Urgent / 🟡 Medium / ⚪ Low
Status:       To Reply
Slack Link:   Full permalink URL (e.g. https://tennrworkspace.slack.com/archives/C.../p...)
Draft Reply:  The drafted reply text
Triaged On:   Today's date
Message TS:   The message_ts value from Slack (e.g. "1775576487.470699")
```

---

## Step 6 — Output the triage list in chat

Present results ordered by priority. For each item:

```
🔴 / 🟡 / ⚪  [Sender] — [#channel or DM] — [time]
[1–2 line message excerpt]
🔗 [Slack link]
────
DRAFT: [reply, ready to copy]
────
```

After the full list, show a summary:
- Total items needing a reply
- Count per priority tier
- Oldest unanswered item
- Link to the Notion database

---

## Step 7 — Also on your radar

After the reply list, add a short section (3–5 items max, one line each + Slack link) for:
- Items where Bruna was CC'd with no direct ask but the thread is active
- Threads where she sent the last message but no one responded (potential nudge)
- Things likely to need a follow-up from her soon

---

## Hard rules

- **Never send messages.** Never call `slack_send_message`. Drafts are for Bruna to copy. Non-negotiable.
- **Always include the Slack permalink** for every item in both the chat output and Notion.
- **Never pad the list** with clearly resolved items.
- **Never explain your process** in the output — just deliver the triage list.
- If search returns no results: tell the user and try expanding time window to 7 days.
