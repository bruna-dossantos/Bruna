# Bruna's Claude Code Setup

## Identity & Context

See `references/context.md` for full work context: name, role, team structure, tone rules by relationship, domain terminology, and priority signals.

## Repository

- **GitHub:** `bruna-dossantos/bruna`
- **Branch convention:** `claude/<descriptor>` (e.g. `claude/fervent-turing-5AAtk`)
- **Always develop on the designated branch. Never push to a different branch without explicit permission. Never create a pull request unless explicitly asked.**

## Skills

### Chief of Staff plugin (`chief-of-staff:*`)

| Skill | Trigger |
|-------|---------|
| `chief-of-staff:morning-command-center` | Brief me, morning brief, daily brief, what's my day, catch me up, command center, what's happening today |
| `chief-of-staff:slack-operator` | Check Slack, triage Slack, slack operator, catch up on Slack, draft my Slack replies, what do I need to respond to |
| `chief-of-staff:meeting-debrief` | Debrief, log the meeting, extract action items, meeting debrief, what came out of my meeting |
| `chief-of-staff:meeting-prep` | Prep for my meeting, meeting prep, prepare for [meeting], get ready for my meeting with [name] |

### Legacy (do not use — superseded by chief-of-staff plugin)

| Skill | Replaced by |
|-------|-------------|
| `slack-reply-triage` | `chief-of-staff:slack-operator` |
| `one-on-one-prep` | `chief-of-staff:meeting-prep` |
| `daily-briefing` | `chief-of-staff:morning-command-center` |

## MCP Integrations

| Integration | Scope |
|-------------|-------|
| Slack | Search public + private channels, DMs, threads |
| Notion | Commitments DB, Open Loops DB, Triage DB, Meeting Notes DB, People Directory, Daily Briefings DB |
| GitHub | `bruna-dossantos/bruna` only |

## Hard Rules

- **Never send Slack messages** — drafts only, Bruna copies them herself
- **Never create a PR** unless explicitly asked
- **Never push to main/master**
- Slack triage: do NOT use `to:me` — use `@bruna` and `bruna` queries instead (Bruna's Slack ID: `U08H0TF168L`)
