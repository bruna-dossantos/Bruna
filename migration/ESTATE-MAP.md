# Estate map — everything under ~/Documents/Claude

Complete disposition for the whole estate, not just skills. Captured 2026-08-14.

## The one rule that fixes the confusion
**A script lives with the thing it serves.**
- A script used by **one project** stays in that project (and the project gets a short README saying what each script does).
- A script reused **across projects** moves to the repo `scripts/` (with provenance) or into the skill that owns it.
- **Nothing shared or reusable lives loose in a project** — that's what makes it confusing to find.

Layers (from the plan): **Context** = what's true · **Agents** = who reasons · **Skills** = how work is done · **Projects** = the actual work/data · **references/** = durable guides · **scripts/** = reusable code.

---

## Top-level areas

| Area | Size | What it is | Proposed home |
|------|------|-----------|---------------|
| **Prompts & Guides** (14 md) | 56K | Durable guides: Criteria Factory Operating Plan, Medical Qualification Criteria Guide, Payer Mapping prompts, Imaging & Testing prompts, Sens Questions Index | **→ repo `references/`** (copy in; these are institutional knowledge) |
| **Projects** (420 files) | 1.6M | The actual work/data library | **Keep in place** as the data library; add a `PROJECT.md` + scripts README per active project |
| **Payer Mapping** (20 files) | 9.2M | Full customer payer-mapping project (BetterNight, Kaba): configs, scripts, data, outputs | **Move under `Projects/`** — it's a project, not a top-level peer. Its scripts stay with it |
| **Experiments** (156 files) | 108K | Criteria-testing harness + eval (its own `.claude/`, src + tests) | **Keep as a sandbox**; it's dev/experiment, not runtime. Consider its own git repo |
| **Artifacts** (35 files) | 20K | Saved Cowork HTML outputs (dashboards, digests) | **Keep** — generated outputs; leave as-is |
| **Scheduled** (11 wrappers) | 16K | Scheduled-task stubs | **Superseded** by repo `automation/manifests/` → Phase 7 archive |
| **skills** (37 files) | 32K | Loose skills | Consolidated into repo (done); originals = Phase 7 archive |
| **Plugins** (6 `.plugin`) | 0B | Source plugin bundles (criteria-toolkit, ea, linear-ops, tennr-ops, toolbox) | **Leave** — these are your plugin sources; verify they're the build source before touching |
| **Archives** (94 files) | 312K | Prior cleanup quarantine (2026-07-22) | **Leave** — already archived |
| **Personal/Finance** | 8K | 🔒 Personal bank/card statements | **LEAVE ALONE — never copy, reference, or move** |

---

## Projects

| Project | What it is | Scripts inside? | Proposed |
|---------|-----------|-----------------|----------|
| **Criteria Updates** (207 files) | The active heart: order-type↔ticket maps, reconciliations, criteria docs | 2 loose | Keep as data library. Add `PROJECT.md`. Move the stray `June24-criteria-toolkit.plugin` out |
| **Criteria Data Metrics** | Snowflake/Metabase SQL for criteria-gen metrics | SQL + 1 py | Keep. ⚠️ **`session token - metabase.txt` is a credential — move to `Credentials/` or delete** |
| **Linear Scripts** (13) | Reusable Linear utilities (get team/workflow UUIDs, customer IDs) + `payer_reconciliation/` | **5 + 5 reusable** | **→ repo `scripts/linear/`** (reusable across work). Big CSV stays as data |
| **J&B Document Criteria** (51) | Project-specific doc-criteria pipeline (`_pipeline/rxproj`, 13 scripts) | 16 project-specific | **Stays with J&B.** Add a scripts README |
| **Document Criteria Method** (4 md) | Reusable mapping/validation RULES (WHATS_REUSABLE, CANONICAL rules) | none | **→ repo `references/` or a `document-criteria` skill** — this is reusable method |
| **Denial Analyzer** (51) | Denial data + CARC/RARC | none | Done: `PROJECT.md` added; method → `skills/rcm/denial-analysis` |
| **DME / Financial** | Industry-intel / financial review | none | Done: `PROJECT.md` added |
| **Customers** (17) | 🔒 Customer onboarding data (HomeMedix etc.) | 1 | **Keep in place — PHI-adjacent, do not relocate** |
| **Interviews** | Hiring interview guides (docx) | none | Keep. Consider moving to an HR area |
| **Linear Master Data** (44) | Source-of-truth CSVs (crosswalk, teams, states) | none | Keep — already the referenced source of truth. 9 `.bak` → archive |
| **Credentials** (7) | 🔒 API tokens & OAuth secrets | n/a | **LEAVE ALONE — never open, copy, or move** |

---

## Scripts index (where every cluster should live)
| Cluster | Count | Owner | Proposed home |
|---------|-------|-------|---------------|
| `Linear Scripts/*` + `payer_reconciliation/*` | 10 | reusable Linear utilities | **repo `scripts/linear/`** |
| `Payer Mapping/scripts/*` | 2 | Payer Mapping project | stays; if `export_insurance_initiative_issues.py` is reused, copy to repo `scripts/` |
| `J&B Document Criteria/_pipeline/**` | 16 | J&B project | stays with project |
| `Experiments/.../criteria-testing/**` | 18 | dev harness | stays in Experiments |
| `Criteria Data Metrics/*.py`, `*.sql` | ~5 | metrics project | stays; token removed |
| loose singletons (Customers/HomeMedix, Criteria Updates) | ~4 | their projects | stay; documented in project README |

## Security flags
1. ✅ **RESOLVED** — `Criteria Data Metrics/session token - metabase.txt` moved to `Credentials/metabase-session-token.txt` (2026-08-14).
2. 🔴 **ACTION NEEDED — rotate tokens.** `Linear Scripts/*.py` had **5 hardcoded live Linear tokens** in plaintext (2 `lin_oauth_`, 3 `lin_api_`). The repo copies in `scripts/linear/` are sanitized (env-var read, no secrets). The **originals still contain the live tokens** — rotate them in Linear and treat as exposed. See `Projects/Linear Scripts/README.md`.
3. ✅ `Credentials/`, `Personal/Finance/`, `Customers/` — left untouched.
