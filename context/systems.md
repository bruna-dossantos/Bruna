# Systems & connectors

Tools Claude can reach on Bruna's behalf (via MCP unless noted).

| System | What it's used for |
|--------|--------------------|
| **Slack** | Triage, mentions, team communication. Search public + private channels, DMs, threads. Bruna's Slack ID: `U08H0TF168L`. |
| **Notion** | Meeting Notes DB, daily-briefing pages, Slack Triage DB, People Directory. |
| **Linear** | Qualification-criteria tracking (DME Criteria + Infusion Criteria teams). |
| **Google Calendar** | Schedule, 1:1s, meeting detection. |
| **Akiflow** | Task scheduling and time-blocking. **Always check Akiflow before creating a duplicate task or recurring block.** |
| **Salesforce** | Pipeline / customer data. |
| **Gong** | Call transcripts and customer insights. |
| **Google Drive / Gmail** | Docs, sheets, email. |
| **Figma** | Design files. |
| **CMS Coverage (Medicare)** | NCD/LCD lookup for Part B coverage policy. |

## Hard rules for connected systems
- **Slack: draft only — never send.** Bruna copies drafts herself. For triage, don't use `to:me`; use `@bruna` and `bruna` queries.
- **Never push to `main`/`master`; never open a PR unless explicitly asked.** Work on a `claude/<descriptor>` branch.
- Least-privilege: request only the access a task needs, especially for healthcare/customer data.

See [[sources-of-truth]] for which data source wins when they disagree.
