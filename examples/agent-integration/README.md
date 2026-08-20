# Mnemovela Agent Integration

Run Mnemovela as a **memory backend for AI coding agents** (OpenCode, Claude Code,
Codex, and any MCP-compatible tool). The agent stores decisions, facts, workspace
state, and project knowledge across sessions, and recalls them at task start.

## How it works

1. **Start the Mnemovela MCP server.** The server binary (`mnemovela-mcp-stdio`) speaks
   the Model Context Protocol over standard input/output. It exposes 25 `mnemovela.*`
   tools across five categories:

   | Category | What it does | Tools |
   |----------|--------------|-------|
   | **Recall** | Retrieve relevant memory before starting work | `search_memory`, `query_facts`, `query_memories`, `build_context` |
   | **Writes** | Persist episodes, facts, knowledge | `add_episode`, `add_fact`, `commit_memory`, `upsert_entity`, `upsert_subject` |
   | **Capture** | Record decisions, errors, tool calls mid-session | `capture_decision`, `capture_error`, `capture_tool_call`, `capture_constraint` |
   | **Session** | Start and end coding sessions with context | `session_start`, `session_end`, `get_context` |
   | **Maintenance** | Branch, merge, extract, invalidate stale facts | `create_branch`, `merge_branch`, `invalidate_fact`, `extract_episode`, `list_branches` |

   Get a binary from the [latest Mnemovela-open release](/releases) and put it on
   your PATH.

2. **Configure your agent's MCP** (see platform configs below). The agent gets a
   "Mnemovela" MCP server it can call for `mneme.search_memory(...)` etc.

3. **Load a companion skill** that tells the agent *when* and *how* to use Mnemovela
   — see the [universal skill](skills/mnemovela-agent-memory/SKILL.md). Without a skill,
   the agent has the tool but doesn't know the memory lifecycle.

## Platform configs

### OpenCode

Copy `opencode.json` into your project root (or merge into an existing one):

```json
{
  "mcp": {
    "Mnemovela": {
      "type": "local",
      "command": ["mnemovela-mcp-stdio"],
      "enabled": true
    }
  }
}
```

If the binary is not on PATH, use an absolute path, e.g.:
`"command": ["D:\\tools\\mnemovela-mcp-stdio.exe"]`.

Then put the [universal skill](skills/mnemovela-agent-memory/SKILL.md) into
`.opencode/skills/mnemovela-agent-memory/SKILL.md` — OpenCode auto-loads it.

### Claude Code

Add the MCP server to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "Mnemovela": {
      "command": "mnemovela-mcp-stdio"
    }
  }
}
```

Then copy the [universal skill](skills/mnemovela-agent-memory/SKILL.md) into your project
as `CLAUDE.md` or a hook that invokes the recall/writeback patterns.

### Codex

Add to `~/.codex/config.toml`:

```toml
[mcp."Mnemovela"]
command = "mnemovela-mcp-stdio"
```

Then either add the skill content to `AGENTS.md` or configure hooks in
`~/.codex/hooks.json` to trigger recall at session-start and writeback at
session-end.

## Companion skill

The **[universal agent-memory skill](skills/mnemovela-agent-memory/SKILL.md)** covers the
full lifecycle:

| Phase | What the agent does |
|-------|---------------------|
| **Start of task** | `search_memory` for related past work + `query_facts` for known constraints/decisions + `build_context` for project state |
| **During work** | `capture_decision` for important design choices, `capture_error` for failures with diagnosis, `add_fact` for durable reusable knowledge |
| **Completion** | `add_episode` summary (changed files, test outcomes, decisions), selective `add_fact` for new module/test relationships, `invalidate_fact` for stale facts |

It also defines the **entity ID convention** (`module:<name>`, `file:<path>`,
`concept:<name>`, `constraint:<name>`, …) and the **fact predicate vocabulary**
(`implements`, `depends_on`, `tested_by`, `known_failure`, `decision`,
`constraint`) — so the knowledge graph stays consistent.

## Getting the binary

Download the latest `mnemovela-mcp-stdio` for your platform from
[GitHub Releases](/releases). The release includes four server binaries:

| Binary | Purpose |
|--------|---------|
| `mnemovela-mcp-stdio` | **MCP server** — the one agents use |
| `mnemovela-jsonrpc-stdio` | JSON-RPC server over stdio (alternative protocol) |
| `mnemovela-http` | HTTP server with REST + JSON-RPC (`/api/v1/jsonrpc`) |
| `mnemovela-grpc` | gRPC server |

All binaries start with an in-memory backend (no persistence). For persistence
across restarts, set `Mnemovela_GO_PEBBLE_PATH=./mneme.pebble` before launching.

## Example: a full session

```
[Agent starts a task "add dark mode toggle"]

Agent: mneme.search_memory(query="dark mode theme", top_k=5)
→ finds: "Previous attempt stalled on CSS variable conflicts"
→ finds: "Constraint: must support system preference detection"

Agent: mneme.query_facts(subject_id="constraint:theme-system-preference")
→ fact: constraint:theme-system-preference = "requires @media (prefers-color-scheme)"

Agent: mnemovela.build_context(query="dark mode UI patterns")
→ returns sections from past episodes about component patterns

[Agent works, adding a theme toggle component...]

Agent: mneme.capture_decision(decision_summary="Use CSS custom properties on :root", rationale="Least churn on existing components", alternatives="Tailwind dark: prefix, separate stylesheets")

Agent: mneme.add_fact(fact_id="fact:dark-mode-implements-css-vars", subject_id="module:theme-provider", predicate="implements", object_value="CSS custom properties approach")

[Agent completes]

Agent: mneme.session_end(summary="Added dark mode toggle. Changed: ThemeProvider.tsx, styles/theme.css, Settings.tsx. Tests: 5/5 pass (npm run test -- Theme). Key decisions: CSS vars approach. Pitfalls: Flash-of-light on initial load — deferred to follow-up.")
```

This gives the next session full context before a single file read. The
companion skill formalizes these patterns so every session follows them.
