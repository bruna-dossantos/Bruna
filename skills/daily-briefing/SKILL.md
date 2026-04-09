---
name: daily-briefing
description: >
  Generate Bruna's daily briefing — a structured morning ops page + company-wide newspaper. Reads Slack Triage DB for personal items (never runs fresh triage searches for this), pulls Google Calendar, detects missing Akiflow blocks, calculates real capacity, scans Slack for Tennr-wide news, reviews recent meeting notes for open action items, creates meeting notes for today's calendar events, and writes a polished Notion page with the newspaper at the bottom. Use whenever Bruna says "brief me", "morning brief", "daily brief", "what's my day", "catch me up", or "what's happening today".
---

# Daily Briefing Skill

Two jobs in one: (1) Bruna's personal ops picture for the day, and (2) a company-wide newspaper so she stays informed on all of Tennr — not just her vertical.

---

## Key IDs

| Resource | ID |
|---|---|
| Command Center hub | `33ceb680-c7fc-815c-bef7-c4e0d8cd9bdf` |
| Daily Briefings DB | `collection://fb0473d1-ff0d-4216-863a-722cb8d2ce6a` |
| Slack Triage DB | `collection://001d2780-bb0e-497c-a4b5-257c7d18334b` |
| Slack Triage — ✅ Mark Done view | `view://33deb680-c7fc-81ad-9636-000ceab718e2` |
| Meeting Notes DB | `collection://1b4eb680-c7fc-802d-94f6-000b412c3dd0` |
| Meeting Notes — 📅 Calendar view | `view://33deb680-c7fc-8111-a47e-000cbcdca657` |
| Working hours | 9am–6pm ET = 540 min = 100% |
| Bruna Notion user | `user://1b1d872b-594c-81ca-a437-000231027524` |

---

## Step 1 — Pull everything in parallel

### 1a. Google Calendar
- `timeMin`: today 00:00 ET · `timeMax`: Friday 23:59 ET
- `condenseEventDetails`: true · `timeZone`: America/New_York

**Event categories:**

| Category | In capacity math? | Show in schedule? |
|---|---|---|
| Personal (Workout, Family Time) | ❌ | ✅ shown, labeled personal |
| Commute | ❌ — dead time, cannot work | ✅ shown, labeled Commute |
| Working Location markers | ❌ | ❌ never shown |
| Meeting (≥2 attendees, external, named recurring) | ✅ | ✅ |
| Akiflow task (single-attendee, Akiflow-created) | ✅ | ✅ |
| Focus blocks | ✅ | ✅ |

**Commute = dead time.** Never count commute in capacity or suggest using it for tasks.
**No RSVP flags anywhere.** Never add RSVP columns, warnings, or flags — Bruna doesn't track these.
**Deduplication:** same time slot → keep the one with more attendees or the task-specific name.

### 1b. Slack Triage DB — personal items only
```sql
SELECT "Message", "Sender", "Channel", "Priority", "Status", "Slack Link", "Draft Reply",
       "date:Triaged On:start"
FROM "collection://001d2780-bb0e-497c-a4b5-257c7d18334b"
WHERE "Status" != 'Done' AND "Status" != 'Skipped'
ORDER BY "Priority" ASC
LIMIT 100
```

**Stale filter — apply before including anything:**
- Exclude if Draft Reply implies already handled ("Confirmed", "Sending now", "Done", "Resolved")
- Exclude if triaged >5 days ago with no new activity likely
- Exclude bot messages and automated notifications
- Include only where Bruna genuinely still needs to act

### 1c. Meeting Notes — scan for open action items
```sql
SELECT url, "Meeting name", "date:Meeting Date:start", "Action Items"
FROM "collection://1b4eb680-c7fc-802d-94f6-000b412c3dd0"
ORDER BY createdTime DESC
LIMIT 5
```
For each note with content: fetch the page, extract open action items (table rows where action is not crossed out or marked done). Flag any with no Akiflow block this week.

### 1d. Broad Slack searches — company newspaper
Run all 7 using `slack_search_public`. NEVER use triage DB for this section.

```
Query 1:  in:#general after:[3 days ago]               limit 15
Query 2:  in:#cx-darr-forecasting after:[7 days ago]   limit 10
Query 3:  in:#gong-repository after:[2 days ago]       limit 10
Query 4:  in:#skills-maxxing after:[3 days ago]        limit 10
Query 5:  shipped launched released after:[5 days ago] limit 10
Query 6:  in:#marketing after:[7 days ago]             limit 10
Query 7:  all hands leadership company after:[7 days]  limit 5
```

---

## Step 2 — Capacity math

**Working day = 9am–6pm = 540 min = 100%**

- Commute → EXCLUDED (dead time)
- Personal events → EXCLUDED
- Working Location markers → EXCLUDED
- Meetings + tasks + focus blocks → INCLUDED

**Capacity % = scheduled work minutes / 540 × 100**

**Real deep work slot** = contiguous unscheduled window ≥ 90 min, no meeting within 15 min on either side. 45–60 min blocks do NOT count.

**Capacity Status:**
| % | Status |
|---|---|
| < 50% | Light |
| 50–69% | Manageable |
| 70–85% | Overloaded |
| > 85% | Maxed |

---

## Step 3 — Today's one thing

Apply in order, stop at first match:
1. Active urgent triage item with hard external deadline today/tomorrow (go-live, UAT, customer commitment)
2. Akiflow task block ≥ 60 min
3. 1:1 requiring prep
4. Earliest Akiflow task

Write as: **[Task]** — [time block] · one sentence why it matters most today.

---

## Step 4 — Create meeting notes for today's events

For each meeting on today's calendar with ≥2 attendees:
1. Check if a meeting note already exists in `collection://1b4eb680-c7fc-802d-94f6-000b412c3dd0` for today's date and this meeting name
2. If not → create one with:
   - `Meeting name`: "[Event title] @[Date] [Time] (EDT)"
   - `date:Meeting Date:start`: today's date · `is_datetime`: 0
   - `Meeting Topic`: infer (1:1, Core, COE, CX, Product, etc.)
   - `Customer Name`: N/A if internal
   - Content: standing agenda template with Goals, Notes, Action Items sections; carry-forward from last note if this is a recurring meeting
3. After creating: add the 📋 link to that meeting's row in the schedule table

---

## Step 5 — Missing Akiflow tasks

Cross-reference triage DB against this week's calendar. Flag items where:
- There is no corresponding Akiflow block this week
- The item has a named deadline OR someone is actively waiting
- The item is not already done or in progress

For each: provide specific suggested time slot for today based on the actual schedule gaps.

---

## Step 6 — Write the brief page

Create a page in `collection://fb0473d1-ff0d-4216-863a-722cb8d2ce6a`.

**Properties:**
```
Date (title):       "Weekday, Month Day Year"
Brief Date:         today's date, is_datetime = 0
Location:           Home / Office / Travel
One Thing:          ≤ 80 chars
Urgent Slack Count: integer (after stale filtering)
Medium Slack Count: integer (after stale filtering)
Deep Work Slots:    integer (≥90 min windows only)
Capacity %:         integer (rounded)
Capacity Status:    Light / Manageable / Overloaded / Maxed
```

**Page structure — in this exact order:**

```markdown
> 🗓️ **[Weekday, Month Day · Location]** · Capacity **[N]%** · [emoji + status] · [N] deep work slots

---

# 🎯 One Thing
[task · time · one sentence why]

---

# ⚡ Day at a Glance
[table: Scheduled | Meetings | Tasks | Deep work | Fragmented free]
[callout if Overloaded or Maxed]

---

# 📅 Today's Schedule
[table: Time | Event | Links]
Notes:
- Every meeting: 📅 link required
- Every 1:1: 📋 Notes link (meeting note URL)
- Every UAT/external meeting: 🔗 Zoom link if in event location
- Every Akiflow task with a Linear ticket: 🔗 ticket link
- Personal and Commute rows: show, label clearly, no links required

---

# 🔴 Needs You Now — [N] Active
[numbered list — stale-filtered, active only]
Each item: **[Sender]** — [one-line description] · [thread →](url) or [DM →](url)

---

# 📌 Missing from Akiflow — Block These Today
[table: Task | Deadline | Suggested Slot | Source]

---

# 📣 From Meeting Notes — Needs an Akiflow Block
[table: Action Item | From | Priority]
Linked to the meeting note page. Only items with no block yet.

---

# ⚠️ Falling Off the Radar
[table: Item | Why it slips | Deadline | Action]

---

# 📆 Rest of Week
[Thu + Fri condensed schedule tables with 📅 links]
[Callout for any scheduling conflicts]

---

# 💬 Honest Read
[3–4 sentences: what today actually is, top 3 things that cannot slide, one honest note]

---
---

# 📰 Tennr Today
> *What a leader at your level should know across the whole company.*

## 🏆 Revenue & Growth
## 🤝 Sales Pipeline
## 🛠️ Product & Customer Pods
## 🤖 AI & Infrastructure
## 📣 Marketing & Brand
## 👥 People & Hiring
```

**Formatting rules:**
- Newspaper at the BOTTOM, after a double `---` divider — always
- No RSVP flag columns anywhere in the brief
- No Day of Week column in any table
- No Capacity Warning text field — use `Capacity %` (number) and `Capacity Status` (select) only
- Commute never counted in capacity
- All 6 newspaper sections always present — write "Nothing notable this week" if sparse
- Gong calls: synthesize in 2–4 sentences, never reproduce verbatim
- All Slack links: `https://tennrworkspace.slack.com/...` or `https://tennr.enterprise.slack.com/...` — never `slackMessage://`
- Callouts for warnings, not inline bold text

---

## Step 7 — Chat summary

```
📅 [Day, Date] · [Location] · [N]% capacity · [Status emoji]

🎯 ONE THING: [task] · [time]

📋 [N] meetings · [N] tasks · [N] deep work slot(s)

🔴 [N] active urgent items
• [Sender] — [summary] → [url]
• ...

📌 Missing blocks ([N]):
• [task] → [slot]

📣 From meeting notes ([N] unblocked):
• [action item] — [meeting name]

📰 Tennr Today:
• [Revenue headline]
• [Pod/sales signal]
• [Company/infra/marketing note]

⚠️ Falling off radar: [N] items

→ Brief: [notion url]
→ Mark triage done: https://www.notion.so/a2fd025820f048d99d373dcdd9b98ec6
→ Meeting calendar: https://www.notion.so/1b4eb680c7fc806096f5d9d903ed5998
```

---

## Hard rules — never break these

- **NEVER** run fresh Slack searches for the triage section — use `collection://001d2780-bb0e-497c-a4b5-257c7d18334b` only
- **DO** run 7 `slack_search_public` queries for the newspaper section
- **NEVER** count commute in capacity — it is dead time
- **NEVER** count 45–60 min blocks as real deep work
- **NEVER** add RSVP flags, RSVP columns, or RSVP warnings anywhere
- **NEVER** add a Day of Week column
- **NEVER** use Capacity Warning text — use Capacity % and Capacity Status properties
- **NEVER** write the brief as qual-only — always cover all pods, verticals, departments
- **NEVER** reproduce Gong summaries verbatim — synthesize only
- **NEVER** include stale or already-handled triage items
- **ALWAYS** put the newspaper at the bottom, after a double `---`
- **ALWAYS** include all 6 newspaper sections
- **ALWAYS** create meeting notes for today's calendar events before writing the brief
- **ALWAYS** scan recent meeting notes for open action items with no Akiflow block
- **ALWAYS** include 📋 links to meeting notes in the schedule table
- **ALWAYS** write to the correct hub: `33ceb680-c7fc-815c-bef7-c4e0d8cd9bdf`
- After delivering chat summary: always include the ✅ Mark Done view link so Bruna can mark items done without hunting for it
