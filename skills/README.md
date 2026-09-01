# Skills

One canonical source per skill, organized by family. Runtime discovery is via symlinks in `.claude/skills/` (and, for some skills, installed plugins). **Do not create a second discoverable copy of a skill a plugin already provides** — keep the authoritative *source* here, let the plugin handle runtime where one exists.

## Families

| Family | Skill | Source | Discovered here? |
|--------|-------|--------|------------------|
| management | one-on-one-prep | repo (was `skills/`) | ✅ `.claude/skills` symlink |
| management | daily-briefing | repo (was `skills/`) | ✅ `.claude/skills` symlink |
| communications | slack-reply-triage | repo (was `skills/`) | ✅ `.claude/skills` symlink |
| qualification | criteria-writer | copied 2026-08-14 from `~/Claude/skills/criteria-writer` | source only |
| qualification | criteria-writer-imaging | copied 2026-08-14 from `~/Claude/skills/criteria-writer-imaging` | source only |
| qualification | full-criteria-factory | repo `criteria-toolkit/skills/` (left in place — heavy venv) | ✅ `.claude/skills` symlink |
| linear | insurance-ticket-sync | repo (was `criteria-toolkit/skills/`) | source only |
| linear | refresh-insurance-issues | repo (was `criteria-toolkit/skills/`) | source only |
| linear | reconcile-order-rules | repo (was `criteria-toolkit/skills/`) | source only |
| matcher | matcher-chat / -linear / -slack / -meetings / -agendas | copied 2026-08-14 from `~/Claude/skills/Bruna Central Database` | source only |
| rcm | denial-analysis | extracted 2026-08-14 from `Denial Analyzer/AGENTS.md` | source only |

## Plugin-provided (NOT duplicated here — edit the plugin, not a loose copy)
`criteria-reviewer`, `criteria-duplicator`, `criteria-evaluation`, `payer-linear-mapper`, `payer-document-matcher`, `insurance-mapper`, `follow-up-tracker`, `team-pulse`, `meeting-notes-review`, `meeting-prep`, and the EA/chief-of-staff family come from installed plugins (ea-plugin, criteria-toolkit, chief-of-staff, linear-ops, anthropic-skills). The orchestrator routes to those directly.

## Known follow-ups
- **`criteria-reuse-finder`** (`~/Claude/skills/`) was renamed from `payer-document-matcher` and rewritten on 2026-08-14 and was being actively edited by another live session during this migration — deliberately NOT copied in yet. Bring it in once stable.
- **full-criteria-factory** still lives under `criteria-toolkit/skills/` (its `.venv` is heavy and gitignored). Fold into `skills/qualification/` in a later, quiet pass; its `.claude/skills` symlink already points at the current location.
- The **matcher** family is copied verbatim; the plan calls for merging it with payer/Linear matchers into one matcher architecture with named adapters — that's a design task, not done here.
