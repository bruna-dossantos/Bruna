# Path reference audit — before moving/archiving

Run 2026-08-14, before executing any Phase 7 move. Question answered: **for every path we plan to move or archive, does anything else depend on it?**

## Method
Searched `~/Projects/Bruna`, `~/Documents/Claude`, and `~/.claude` for path-shaped references in code/config/doc text (`*.md/.json/.py/.sh/.txt/.toml/.yaml/.yml/.cfg`), excluding `.git`, venvs, `site-packages`, `__pycache__`, `node_modules`, plugin `marketplaces`, `Archives`, and git `worktrees`. Also checked: all symlinks in those roots, and both live schedulers.

## Result: SAFE — no runtime dependency on any candidate

| Candidate to move/archive | Referenced by | Verdict |
|---|---|---|
| `~/Documents/Claude/skills/criteria-writer` (+ `-imaging`) | only migration docs (MIGRATION, README, baseline) | ✅ safe |
| `~/Documents/Claude/skills/Bruna Central Database` | migration docs + SKILLS-LOG + Claude/README (mentions, not deps) | ✅ safe |
| `~/Documents/Claude/Scheduled/*` (11 wrappers) | only the `automation/manifests/*` (which record the path by design) + baseline | ✅ safe |
| `payer-document-matcher.zip` | only MIGRATION.md | ✅ safe |
| `.venv-sheets`, `__pycache__`, `.bak` files | only EXCLUSIONS/MIGRATION docs | ✅ safe |

### Checks that came back empty (good)
- **Symlinks:** no symlink in any root points into a candidate path.
- **Live schedulers:** `scheduled-tasks` MCP → *no tasks*; `CronList` → *no jobs*. The `Scheduled/` wrappers are inert — nothing fires them.
- **Repo-internal moves already done** (EA skills → families; `criteria-toolkit/skills/*` → `skills/linear/`): **no stale references to the old locations** anywhere. Those moves are clean.
- **Plugin sources:** `~/Documents/Claude/Plugins/*.plugin` are empty stubs (0 B); the repo `criteria-toolkit/skills` is not a live plugin build source.

## Scope caveat
Only text code/config/doc types were scanned. Binary/office files (`.xlsx`, `.docx`, `.html`, `.ipynb`) were not grepped — a path sitting in a spreadsheet cell or HTML artifact is data, not a runtime dependency, so a move won't break execution. If you want, I can scan those too before archiving.

## Bottom line
Everything queued for Phase 7 is free of runtime dependencies. The only things that "reference" these paths are the migration documents and the automation manifests, and both are *supposed* to record the old location. Archiving is safe whenever you give the go-ahead.
