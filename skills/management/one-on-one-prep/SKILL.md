---
name: one-on-one-prep
description: >
  Generate a new 1:1 meeting note in the Notion Meeting Notes database, pre-populated with the meeting details from Google Calendar. Use this skill whenever Bruna asks to prep for a 1:1, create meeting notes, set up an agenda for an upcoming 1:1, or "get ready for my meeting with [name]". Also triggers for phrases like "create a 1:1 note", "add meeting notes for my 1:1", "prep my next 1:1 with [name]", or "log my 1:1 with [name]". Always use this skill for 1:1 meeting note creation — don't try to create Notion pages manually without it.
---

# 1:1 Meeting Note Generator

Create a properly structured 1:1 meeting note in Notion, linked to the correct People Directory entry, with attendees pre-tagged, and the agenda scaffold ready to fill in.

---

## Key IDs

**Meeting Notes Database:**
- Data Source ID: `collection://1b4eb680-c7fc-802d-94f6-000b412c3dd0`
- Database URL: `https://www.notion.so/1b4eb680c7fc806096f5d9d903ed5998`

**People Directory:**
- Data Source ID: `collection://ae695dac-2bd0-4b7b-94bf-6ff710d8d3c5`
- Database URL: `https://www.notion.so/21fa593b1e6e43a6bc18a33cda97bd84`

**Bruna's Notion User ID:** `user://1b1d872b-594c-81ca-a437-000231027524`
**Bruna's email:** `bruna@tennr.com`

**Known People — all IDs needed for the skill:**

| Name | Notion User ID | Slack User ID | Calendar Email | People Directory URL | Direct Report? |
|------|---------------|---------------|----------------|---------------------|---------------|
| Mary Cleary | `user://310d872b-594c-810d-a63f-0002adaf88d2` | `U0AGESY5ZHC` | `mary.cleary@tennr.com` | `https://www.notion.so/313eb680c7fc81339f61e911409142e3` | ✅ Yes |
| Sean Becker | `user://2cad872b-594c-81a4-9e57-000220c05282` | `U0A3FU6KZM1` | `sean.becker@tennr.com` | `https://www.notion.so/313eb680c7fc81ca836be5580cbe39c1` | ✅ Yes |
| Rachel Duda | `user://262d872b-594c-812a-9d88-0002c08d7f89` | `U09D4GEFM0W` | `rachel.duda@tennr.com` | `https://www.notion.so/313eb680c7fc81169252f2a4c60742ad` | ✅ Yes |
| Stacey Wisniewski | `user://211d872b-594c-8135-9ea9-00028434b8a2` | `U090Y68BYP9` | `stacey.wisniewski@tennr.com` | `https://www.notion.so/313eb680c7fc81eb95ecc36e2c623be3` | ✅ Yes |
| Tess L'Olivier-Lam | `user://30ad872b-594c-8141-ab3d-000240dd84ad` | `U0AFDAK96KU` | `tess@tennr.com` | `https://www.notion.so/313eb680c7fc8145b058c6165e3f9818` | ✅ Yes |
| Sen Zhang | `user://248d872b-594c-8103-9a2b-00027210e5a9` | `U099JTADQ4C` | `sen@tennr.com` | `https://www.notion.so/313eb680c7fc81f1b9e5e0a86210b731` | No (manager) |
| Jackson Wood | `user://2bd99796-7e01-4d27-aefa-58332e516f0f` | `U06DRBWGK7A` | `jackson@tennr.com` | `https://www.notion.so/313eb680c7fc81379cbad59013010181` | No |
| Matt Dillabough | `user://742d1b2b-6f8e-400b-bd11-1b95884b97a8` | `U05AMMD3C1J` | `matt@tennr.com` | `https://www.notion.so/313eb680c7fc814a9332cb2e2e7eb7b4` | No |
| Genevieve Payzer | `user://24cd872b-594c-8198-bed1-0002702c92c4` | `U099RU2SQHK` | `genevieve@tennr.com` | `https://www.notion.so/313eb680c7fc8117bbfce755359b72b4` | No |
| Claire North | `user://1f4d872b-594c-8158-b9da-0002b1f5beb2` | `U08SCTK6CMR` | `claire@tennr.com` | `https://www.notion.so/313eb680c7fc810d9e6bfd32a6065807` | No |
| Saranga Arora | `user://245d872b-594c-81c9-8f2c-0002e95c14ed` | `U098SE7MY74` | `saranga@tennr.com` | `https://www.notion.so/313eb680c7fc814585f4df788bdd560e` | No |
| Jasper Wu | `user://231d872b-594c-8147-af80-0002e4d51153` | `U095VGX4BV0` | `jasper.wu@tennr.com` | `https://www.notion.so/313eb680c7fc811ebb2ad257856f9c88` | No |

**Bruna's Slack ID:** `U08H0TF168L`

---

## Step 1 — Identify the meeting

If Bruna named the person (e.g. "prep my 1:1 with Mary" or "prep my 1:1 with Stacey"), use that name to look them up in the table above. Otherwise, check Google Calendar for upcoming 1:1 meetings using `gcal_list_events` for today and the next 7 days, filtering by `q="1:1"`. Compare attendee emails against the Calendar Email column in the table to identify who the meeting is with.

**What counts as a 1:1:**
- Title contains "1:1", "1on1", "sync", or just "Name & Bruna" / "Bruna & Name"
- Exactly 2 human attendees (ignore @resource.calendar.google.com entries)

If multiple 1:1s are upcoming, ask Bruna which one she wants to prep. If she said "my next 1:1", pick the earliest upcoming one.

---

## Step 2 — Resolve the person

Once you know who the meeting is with:

1. Find their **People Directory page URL** from the table above (or search `notion-search` if not listed)
2. Find their **Notion user ID** — use `notion-search` with `query_type: "user"` and their name if not in the table
3. Determine if they are a **Direct Report** (see Direct Reports list above)

---

## Step 3 — Gather intel (run all of these before writing the page)

Do all of the following before creating the note. The goal is to walk in knowing what actually happened since the last 1:1.

### 3a. People Directory page
Fetch the person's People Directory page. Extract:
- Open Follow-Ups / Action Items (with owners — note which are Bruna's vs theirs)
- "🎯 Agenda for Next 1:1" section if present
- Last Meeting date, Mood / Tone, Role / Context, Notes

### 3b. Previous meeting notes (last 2)
Search the Meeting Notes database for the last 2 meetings with this person:
```
notion-search: "[First Name] Bruna 1:1"
data_source_url: collection://1b4eb680-c7fc-802d-94f6-000b412c3dd0
```
Fetch the most recent 1–2 results. Extract:
- All action items (who owns each, what was the specific ask)
- Key discussion topics and decisions
- Any explicitly flagged follow-ups or blockers

**Cross-reference**: Compare action items from prior notes to determine which are **still open** (not mentioned as resolved in any subsequent note). These become the Carried Forward section.

### 3c. Slack — recent activity (public AND private)
Use `slack_search_public_and_private` (not `slack_search_public`) to cover DMs and private channels.

Run two queries since the last 1:1 date:
```
Query 1: "from:[first.last@tennr.com] after:YYYY-MM-DD"
Query 2: "[First Name] [Last Name] after:YYYY-MM-DD"
```

Also check the DM thread directly using `slack_read_channel` with their Slack user ID as the channel_id — this surfaces direct message history that search may miss.

Look for:
- Escalations or blockers they raised (DMs to Bruna especially)
- Things they asked for help on that haven't been resolved
- Wins, progress calls-outs, or notable work completed
- Issues flagged about team members, customers, or processes
- Anything that has been sitting unanswered

Synthesize signals into 2–3 bullets for the Discussion section. If nothing surfaces, note "No Slack signals found since [date]" in the note.

---

## Step 4 — Create the Notion page

Create a new page in the **Meeting Notes** data source.

### Properties to set:

```
Meeting name:      "[Person First Name] & Bruna 1:1 [date mention-date]"
Meeting Topic:     "1:1"
Attendees:         [Bruna's user ID, Person's user ID]
People Directory:  [Person's People Directory page URL]  ← CRITICAL: always link this
Follow Up Required: false
Tasks:             false
Customer Name:     ["N/A"]
```

### Page title format:
```
[First Name] & Bruna 1:1 @[Month Day, Year HH:MM AM/PM (TZ)]
```
Example: `Mary & Bruna 1:1 @April 10, 2026 11:00 AM (EDT)`

### Page content — use this structure, fully populated from your research:

```markdown
## 🔴 Carried Forward
> [Action items from previous 1:1s that are not yet confirmed resolved. List with owner.]
> If none: "No open items from last meeting."

| # | Action Item | Owner |
|---|-------------|-------|
| 1 | [specific item from notes] | [Bruna / Person] |

---

## 🟠 Discussion

**[Topic pulled from last meeting or Slack signal]**
- [Specific question or check-in based on real context]

**[Second topic]**
- [Specific follow-up]

---

## 🟡 Standing Questions

**What's going well?**

**What's not working?**

**Where do you need me?**

---

## 🌱 Growth & Coaching
[Pull from People Directory coaching notes or growth areas. 1–2 questions, not generic.]

---

## 📝 Notes


---

## ✅ Action Items

| Owner | Action | Due |
|-------|--------|-----|
| | | |
```

**Quality bar**: The Carried Forward and Discussion sections must be populated with real content from the research steps. Never leave them generic. If you found nothing (truly no prior notes, no Slack activity), say so explicitly in the note so Bruna knows the context gap.

---

## Step 5 — Confirm with Bruna

After creating the page, give Bruna a quick brief in chat:
- Notion page link
- Meeting date/time and who it's with
- How many carried-forward items you found (and from which meeting date)
- Any notable Slack signal if you found one (e.g. "Stacey flagged a blocker in #criteria last week")

4–6 lines max. Don't recite the full agenda — Bruna can open the note.

---

## Hard Rules

- **Always** do the intel steps (3a, 3b, 3c) before creating the page — never skip research
- **Always** populate Carried Forward with real items from notes; never leave it generic
- **Always** include the three standing questions verbatim: "What's going well / What's not working / Where do you need me"
- **Always** set the `People Directory` relation property
- **Always** include both Bruna and the other person in `Attendees`
- **Always** set `Meeting Topic` to `"1:1"`
- **Never** create the page under the wrong data source — use `collection://1b4eb680-c7fc-802d-94f6-000b412c3dd0`
- If you can't find the person in the People Directory, create the note anyway but flag to Bruna
