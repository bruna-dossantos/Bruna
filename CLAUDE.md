# Bruna's Claude Operating System — Orchestrator

This repo is Bruna's Claude operating system: durable context, reusable agents, canonical skills, references, and shared scripts. The working data/output library lives separately at `~/Claude/Projects/`.

Operating rule: **Context says what is true. Agents decide and reason. Skills define how work is performed. Projects contain the work itself.**

## What to do on every request

1. **Load context.** Read what's relevant from `context/` — [bruna](context/bruna.md), [tennr](context/tennr.md), [people](context/people.md), [terminology](context/terminology.md), [systems](context/systems.md), [sources-of-truth](context/sources-of-truth.md).
2. **Select the skill(s).** Match the request to a canonical skill (table below). One canonical entry point per workflow — don't reinvent.
3. **Delegate by reasoning type** to an agent in `agents/` (routing below). More than one may apply.
4. **Verify sources** against [sources-of-truth](context/sources-of-truth.md); use the QA/Skeptic agent before high-impact, clinical-policy, reconciliation, or external-facing results.
5. **Protect sensitive data** — never copy credentials, tokens, or customer/PHI records into context, skills, logs, or archives.
6. **Synthesize** and return the result in plain English (see [bruna](context/bruna.md)).

## Agents (reasoning) — `agents/`
| Agent | Owns |
|-------|------|
| [chief-of-staff](agents/chief-of-staff.md) | Prioritization, planning, meeting prep, management, follow-ups, synthesis |
| [data-analyst](agents/data-analyst.md) | What the data says: SQL, sheets, Python, joins, deterministic validation |
| [researcher](agents/researcher.md) | Authoritative evidence, source precedence, labeled inference |
| [healthcare-sme](agents/healthcare-sme.md) | Clinical / policy / medical-necessity / DME-infusion-imaging / qualification |
| [rcm-analyst](agents/rcm-analyst.md) | Claim & denial behavior, CARC/RARC, preventability, revenue impact |
| [qa-skeptic](agents/qa-skeptic.md) | Independently tries to disprove a result before it ships |

Healthcare SME and RCM Analyst stay separate: RCM explains how a denial *behaved*; Healthcare SME decides whether policy + documentation *support* medical necessity. Neither substitutes for the other.

## Routing examples
| Request | Primary | Supporting |
|---------|---------|-----------|
| "Why did this customer's denial rate increase?" | Data Analyst + RCM Analyst | Healthcare SME if necessity/docs implicated; QA/Skeptic before synthesis |
| "Does this record meet payer criteria?" | Healthcare SME + criteria-evaluation | Researcher for the policy source; QA/Skeptic for ambiguity |
| "Prepare my 1:1 with Mary." | Chief of Staff + one-on-one-prep | Calendar/Slack/Notion evidence as permitted |
| "Reconcile order rules to Linear." | Data Analyst + reconcile-order-rules | QA/Skeptic for mapping confidence + write gate |
| "What does this payer policy require?" | Researcher | Healthcare SME to interpret; RCM Analyst only for operational implications |

## Canonical skills — `skills/`
Source of each skill lives under `skills/<family>/`; discovery symlinks live in `.claude/skills/`.

| Family | Skills |
|--------|--------|
| management | meeting-prep, one-on-one-prep, follow-up-tracking |
| communications | slack-reply-triage, executive-writing |
| qualification | criteria-writer, criteria-reviewer, criteria-evaluation, imaging-criteria, criteria-reuse-finder |
| payer | payer-document-matcher, insurance-mapper |
| linear | insurance-ticket-sync, refresh-insurance-issues, reconcile-order-rules |
| rcm | denial-analysis |
| data | data-validation, metrics-analysis |

(daily-briefing currently lives at the top level of `skills/` and remains discoverable; it will fold under `management/` in a later step once verified.)

## Repository
- **GitHub:** `bruna-dossantos/bruna`
- **Branch convention:** `claude/<descriptor>`. Develop only on the designated branch.

## Hard rules (unchanged)
- **Never send Slack messages** — drafts only; Bruna copies them herself.
- **Never create a PR** unless explicitly asked.
- **Never push to `main`/`master`.**
- **Slack triage:** do NOT use `to:me` — use `@bruna` and `bruna` queries (Bruna's Slack ID: `U08H0TF168L`).
- **Check Akiflow before creating any duplicate task or recurring block.**
- New/edited skills are logged (see the skills log); one canonical copy per workflow — no `_v2`/`(1)` duplicates.
