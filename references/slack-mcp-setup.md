# Slack MCP Setup Guide

This guide explains how to wire up the Slack MCP server so the `slack-reply-triage` skill can actually query your Slack workspace.

---

## What the Skill Needs

The skill calls four Slack tools:

| Tool name | Used for |
|-----------|----------|
| `slack_search_public_and_private` | Full-text search across channels and DMs |
| `slack_read_channel` | Read recent messages in a specific channel or DM |
| `slack_read_thread` | Fetch the full reply thread for a message |
| `slack_search_users` | Look up user IDs by display name or email |

These are provided by a Slack MCP server. If any of these are missing, the skill will fall back to noting items as "unable to check" for manual review.

---

## Step 1 — Choose an MCP Server

Use the **official Slack MCP server** maintained by Anthropic/the community:

```
npx -y @modelcontextprotocol/server-slack
```

Or install it globally:

```bash
npm install -g @modelcontextprotocol/server-slack
```

---

## Step 2 — Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App → From scratch**
2. Give it a name (e.g. "Claude Triage") and select your workspace
3. Under **OAuth & Permissions → Scopes → User Token Scopes**, add:

| Scope | Required for |
|-------|-------------|
| `search:read` | `slack_search_public_and_private` |
| `channels:history` | `slack_read_channel` (public channels) |
| `groups:history` | `slack_read_channel` (private channels) |
| `im:history` | `slack_read_channel` (DMs) |
| `mpim:history` | `slack_read_channel` (group DMs) |
| `channels:read` | Listing channels |
| `groups:read` | Listing private channels |
| `im:read` | Listing DMs |
| `users:read` | `slack_search_users` |
| `users:read.email` | Looking up users by email |

4. Click **Install to Workspace** and copy the **User OAuth Token** (starts with `xoxp-`)

> Use a **User token** (`xoxp-`), not a Bot token (`xoxb-`). The search API requires user-level auth to access private channels and DMs.

---

## Step 3 — Configure Claude Code

Add the Slack MCP server to your Claude Code settings. Edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxp-your-user-token-here",
        "SLACK_TEAM_ID": "TXXXXXXXX"
      }
    }
  }
}
```

Replace:
- `xoxp-your-user-token-here` → your User OAuth Token from Step 2
- `TXXXXXXXX` → your Slack workspace Team ID (find it in your workspace URL: `https://app.slack.com/client/TXXXXXXXX/...`)

---

## Step 4 — Verify

Restart Claude Code (or reload the MCP server), then run:

```
/mcp
```

You should see `slack` listed as a connected server with the four tool names available.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `slack_search_public_and_private` returns no DM results | Ensure you're using a User token (`xoxp-`), not a Bot token |
| Permission denied on private channels | Add `groups:history` and `groups:read` scopes, reinstall the app |
| Tool not found | Confirm the MCP server is listed in `/mcp` and the server started without errors |
| Search returns stale results | Slack search index can lag ~1 min; retry after a brief wait |
