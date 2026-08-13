# Skills Map — ~/Projects/Bruna

**What this repo is:** the *workshop* where skills are built and edited. It is **not**
what runs day-to-day — the skills that actually run are the **installed plugin** versions.
Editing a skill here does nothing to the live one until it's packaged/installed.

_Last mapped: 2026-08-13._

## The 7 skills and where they live

| Skill | Folder | Saved in git? | Also installed as a plugin? |
|-------|--------|---------------|------------------------------|
| daily-briefing | `skills/` | ✅ | yes (ea-plugin) |
| one-on-one-prep | `skills/` | ✅ | yes (ea-plugin) |
| slack-reply-triage | `skills/` | ✅ | yes (ea-plugin) |
| insurance-ticket-sync | `criteria-toolkit/skills/` | ✅ | yes (criteria-toolkit) |
| reconcile-order-rules | `criteria-toolkit/skills/` | ✅ | yes (criteria-toolkit) |
| refresh-insurance-issues | `criteria-toolkit/skills/` | ✅ | yes (criteria-toolkit) |
| imaging-criteria-extractions | `criteria-toolkit/skills/` | ✅ (rescued 2026-08-13) | not yet |

## The two skill folders (why it feels split)
- **`skills/`** — the EA/ops skills.
- **`criteria-toolkit/skills/`** — the criteria + Linear skills, alongside their `scripts/`.
- **`.claude/skills/`** — NOT a third copy. These are **shortcuts (symlinks)** into the two
  folders above, so Claude Code auto-discovers the skills when you work in this repo.

## Git state (the real source of "everywhere")
- **~23 branches.** Only a couple are merged into `main`; the rest hold in-progress work from
  separate Claude sessions. That's why a skill can look like it exists in several places.
- **Several worktrees** (`.claude/worktrees/…`) — extra "windows" into the repo left over from
  past sessions.
- **Rule going forward:** junk (`.DS_Store`, `__pycache__`, `*.zip`) is now git-ignored.

## If you want to know "what's the real version of skill X?"
1. The **installed plugin** is what runs.
2. The **saved (committed) copy on `main`** is the latest blessed source.
3. Anything only on a feature branch is **work in progress**, not yet blessed.
