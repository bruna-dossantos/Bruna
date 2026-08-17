# Migration exclusions

The following are deliberately EXCLUDED from checksums, copies, and archives:

- **Secrets / tokens**: `~/Documents/Claude/Projects/Credentials/` (linear_tokens.json etc.), any connector auth. Never copied into repo, context, logs, or archives.
- **Generated dependencies**: `.venv`, `.venv-sheets`, `site-packages`, `__pycache__`, `*.pyc`, `node_modules`. Regenerable; archived (not deleted) in Phase 7.
- **Customer records / PHI**: `~/Documents/Claude/Projects/Customers/**`. Referenced by canonical path only; not relocated.
- **Application state**: `~/Library/Application Support/Claude`, Cowork VM bundles, session env. Left alone.
- **Git worktrees**: `.claude/worktrees/**`. Audited separately; not archived in this pass.
