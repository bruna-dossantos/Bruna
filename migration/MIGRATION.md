# Architecture migration — manifest

**Branch:** `claude/architecture-migration` · **Started:** 2026-08-14 · **Mode:** additive / non-destructive
**Plan:** `claude-architecture-migration-plan.md` (Bruna) · **Path decisions validated:** `claude-path-decisions.csv` (Chat)

## Executive status
Consolidation, not reset. The repo (`~/Projects/Bruna`) is now the Claude operating system (context + agents + skills + automation). `~/Documents/Claude/Projects` stays the data library. Nothing has been deleted. Skills from outside the repo were **copied in**, not moved, and originals are untouched.

> ⚠️ **Concurrency note:** during this migration, `ListAgents` showed 3 other live Claude sessions, one actively editing `~/Documents/Claude/skills/` (it renamed `payer-document-matcher` → `criteria-reuse-finder` mid-run). Because of that, all physical removal/archival of files outside this repo is deferred to the **Phase 7 proposal below** and awaits Bruna's go-ahead at a quiet moment.

## What changed in the repo (traceable)

| Item | From | To | Method |
|------|------|----|--------|
| one-on-one-prep | `skills/one-on-one-prep` | `skills/management/one-on-one-prep` | `git mv` + symlink repoint |
| daily-briefing | `skills/daily-briefing` | `skills/management/daily-briefing` | `git mv` + symlink repoint |
| slack-reply-triage | `skills/slack-reply-triage` | `skills/communications/slack-reply-triage` | `git mv` + symlink repoint |
| insurance-ticket-sync | `criteria-toolkit/skills/` | `skills/linear/` | `git mv` |
| refresh-insurance-issues | `criteria-toolkit/skills/` | `skills/linear/` | `git mv` |
| reconcile-order-rules | `criteria-toolkit/skills/` | `skills/linear/` | `git mv` |
| criteria-writer | `~/Documents/Claude/skills/` | `skills/qualification/` | **copy** (original kept) |
| criteria-writer-imaging | `~/Documents/Claude/skills/` | `skills/qualification/` | **copy** (original kept) |
| Bruna Central Database matchers | `~/Documents/Claude/skills/` | `skills/matcher/` | **copy** (original kept) |
| denial-analysis (method) | `Denial Analyzer/AGENTS.md` | `skills/rcm/denial-analysis/` | extracted |

New additive: `context/` (6), `agents/` (6), `automation/manifests/` (13), `skills/README.md`, `CLAUDE.md` rewritten (old kept as `CLAUDE.md.pre-migration-2026-08-14`), `PROJECT.md` added to Denial Analyzer / DME / Financial (existing `AGENTS.md` kept).

## Phase status
- **0 Baseline** ✅ `migration/baseline-2026-08-14/` (skill inventory, instruction files, checksums, git state, exclusions)
- **1 Shadow structure** ✅ context/agents/skills-families/automation created additively
- **1b Context + agents + orchestrator** ✅ 6 context files, 6 agents, orchestrator CLAUDE.md (old backed up)
- **2 De-duplicate skills** ✅ canonical sources consolidated into repo families; discovery symlinks verified
- **3 Project splits** ✅ PROJECT.md added; denial method → skill (non-destructive)
- **5 Automation manifests** ✅ 13 manifests + INDEX with consolidation map
- **4/6 Verify routing & discovery** ✅ symlinks resolve (see verification below)
- **7 Archive** ⏳ **PROPOSAL ONLY — awaiting Bruna's approval** (below)

## Phase 7 — archive proposal (NOT executed)
Move to a dated read-only bundle `~/Documents/Claude/Archives/architecture-migration-2026-08-14/` with a manifest + checksums. Reversible. No permanent deletion.

**A. Generated junk (validated safe — Chat's ARCHIVE list, all regenerable):**
- `~/Documents/Claude/Projects/.venv-sheets/` and all `__pycache__/` under Projects
- repo `criteria-toolkit/**/.venv` + `__pycache__` (already gitignored; 91M — can just delete/regenerate)

**B. Superseded backups:**
- 9 dated `*.bak_*` files in `Linear Master Data/` (crosswalk/teams/states backups)
- `~/Documents/Claude/skills/payer-document-matcher.zip` (superseded by the criteria-reuse-finder rename)

**C. Loose skill originals — ONLY after repo copies are validated AND live sessions are done:**
- `~/Documents/Claude/skills/criteria-writer`, `criteria-writer-imaging`, `Bruna Central Database`
- `~/Documents/Claude/Scheduled/` wrappers superseded by `automation/manifests/` (11 folders) — keep schedule intent, which is now captured in the manifests

**Do NOT archive:** Credentials/, Customers/ (PHI), git worktrees, application state, and `criteria-reuse-finder` (in active use).

## Rollback
- Repo changes: `git checkout main` (this work is isolated on `claude/architecture-migration`).
- Orchestrator: restore `CLAUDE.md.pre-migration-2026-08-14`.
- Copies-in: delete the new family folders; originals were never touched.
