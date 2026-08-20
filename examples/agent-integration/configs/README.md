# Ready-to-copy MCP configs for agent platforms

Each platform needs a small config change to register the Mnemovela MCP server.
Copy the relevant snippet into your config file and restart the agent.

## OpenCode (`opencode.json`)

Merge into your project's `opencode.json` (or create one):

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

If the binary is not on PATH, use the absolute path:
```json
"command": ["/usr/local/bin/mnemovela-mcp-stdio"]
```
or on Windows:
```json
"command": ["C:\\tools\\mnemovela-mcp-stdio.exe"]
```

For Pebble persistence (survives restarts), add an env var:
```json
{
  "mcp": {
    "Mnemovela": {
      "type": "local",
      "command": ["mnemovela-mcp-stdio"],
      "enabled": true,
      "env": {
        "Mnemovela_GO_PEBBLE_PATH": "./.mneme/mneme.pebble"
      }
    }
  }
}
```

The companion skill goes into `.opencode/skills/mnemovela-agent-memory/SKILL.md` —
OpenCode auto-loads it.

## Claude Code (`~/.claude/settings.json`)

Merge into `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "Mnemovela": {
      "command": "mnemovela-mcp-stdio"
    }
  }
}
```

With persistence:
```json
{
  "mcpServers": {
    "Mnemovela": {
      "command": "mnemovela-mcp-stdio",
      "env": {
        "Mnemovela_GO_PEBBLE_PATH": "./.mneme/mneme.pebble"
      }
    }
  }
}
```

To load the skill, either merge the [companion skill](../skills/mnemovela-agent-memory/SKILL.md)
content into your project's `CLAUDE.md`, or set up a hook that invokes the
recall/writeback patterns at session boundaries.

## Codex (`~/.codex/config.toml`)

Add to `~/.codex/config.toml`:

```toml
[mcp."Mnemovela"]
command = "mnemovela-mcp-stdio"
```

With persistence:
```toml
[mcp."Mnemovela"]
command = "mnemovela-mcp-stdio"

[mcp."Mnemovela".env]
Mnemovela_GO_PEBBLE_PATH = ".mneme/mneme.pebble"
```

To load the companion skill, include its content in your project's `AGENTS.md`
or configure hooks in `~/.codex/hooks.json` that trigger `mneme.search_memory`
at session-start and `mneme.session_end` at session-end.
