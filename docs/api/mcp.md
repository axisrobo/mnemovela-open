# Mneme MCP Server

## Overview

Mneme implements a **Model Context Protocol (MCP)** server over stdio, exposing memory tools to LLM agents and IDEs. The server communicates via JSON-RPC 2.0 over stdin/stdout, following the MCP specification (protocol version `2024-11-05`).

**Launch**

| Runtime | Command | Storage | Env override |
|---------|---------|---------|-------------|
| Go | `go run ./cmd/mnemovela-mcp-stdio` | In-memory (default) or Pebble | `Mnemovela_GO_PEBBLE_PATH` |
| Python | `mnemovela-mcp-stdio` | SQLite | `Mnemovela_MCP_DATABASE_PATH` |

Purpose: an IDE or agent host launches the server as a child process and communicates via the MCP lifecycle to discover and invoke `mnemovela.*` tools for memory operations.

## Lifecycle

The MCP interaction follows these steps:

1. **`initialize`** -- The client sends capabilities and protocol version. The server responds with `protocolVersion`, `serverInfo`, and `capabilities.tools`.

2. **`tools/list`** -- The client requests the tool catalog. The server returns an array of tool descriptors, each with `name`, `description`, and `inputSchema`.

3. **`tools/call`** -- The client invokes a tool by name with `arguments`. The server delegates to the JSON-RPC dispatch layer and returns an MCP content response.

4. **`notifications/initialized`** -- Acknowledged with an empty result.

The server reads one line per JSON request and flushes one line per JSON response.

## Tool catalog

The following table lists every `mnemovela.*` tool exposed by the MCP server. The Go runtime exposes 14 tools; the Python runtime exposes 24 (a superset including session management, capture operations, context building, ingestion, and connector sync). Tools marked **(Python)** are Python-only.

| Tool | Runtime | Purpose |
|------|---------|---------|
| `mnemovela.add_episode` | Go, Python | Record a raw episode of agent interaction. |
| `mnemovela.add_fact` | Go, Python | Assert a temporal fact about a subject. |
| `mnemovela.commit_memory` | Go, Python | Commit structured memory (frame, list, hierarchy, etc.). |
| `mnemovela.create_branch` | Go, Python | Create a new branch, optionally from an existing branch. |
| `mnemovela.extract_episode` | Go, Python | Extract frames from a raw episode commit. |
| `mnemovela.invalidate_fact` | Go, Python | Mark a fact as invalidated (non-destructive). |
| `mnemovela.merge_branch` | Go, Python | Merge one branch into another. |
| `mnemovela.query_facts` | Go, Python | Query facts with optional filters. |
| `mnemovela.query_memories` | Go, Python | List committed memory frames on a branch. |
| `mnemovela.resolve_entity` | Go, Python | Resolve a text mention to a known entity. |
| `mnemovela.resolve_entity_explained` | Go, Python | Resolve a text mention with explanation output. |
| `mnemovela.search_memory` | Go, Python | Hybrid (keyword + vector) search across memory. |
| `mnemovela.upsert_entity` | Go, Python | Create or update a knowledge entity. |
| `mnemovela.upsert_subject` | Go, Python | Create or update a subject (agent, user, system). |
| `mnemovela.build_context` | **(Python)** | Build a retrieval-augmented context snippet for a query. |
| `mnemovela.capture_constraint` | **(Python)** | Capture a constraint or rule for future agent behavior. |
| `mnemovela.capture_decision` | **(Python)** | Capture a decision made during an agent session. |
| `mnemovela.capture_error` | **(Python)** | Capture an error encountered during an agent session. |
| `mnemovela.capture_tool_call` | **(Python)** | Capture a tool invocation from an agent session. |
| `mnemovela.get_context` | **(Python)** | Alias for `build_context`. |
| `mnemovela.ingest` | **(Python)** | Ingest a file into memory (multi-modal). |
| `mnemovela.list_branches` | **(Python)** | List all branches, optionally filtered by status. |
| `mnemovela.session_end` | **(Python)** | Capture a session summary and decisions at session end. |
| `mnemovela.session_start` | **(Python)** | Build context for a new agent session. |
| `mnemovela.sync_connector` | **(Python)** | Sync files from an external connector. |

Python tools provide rich `inputSchema` JSON Schema definitions with typed `properties`, `required` fields, and `additionalProperties` constraints. Go tools use a permissive schema (`additionalProperties: true`).

## Example `tools/call`

### search_memory

Request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "mnemovela.search_memory",
    "arguments": {
      "query": "login form bug fix",
      "branch_name": "main",
      "top_k": 5
    }
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "isError": false,
    "content": [
      {
        "type": "text",
        "text": "[{\"commit_id\":\"b7a3f1c2-...\",\"score\":0.92,\"frame\":{...}}]"
      }
    ]
  }
}
```

On error, `isError` is `true` and the text content contains a JSON-encoded error object.

## Edition notes

- `extract_episode`'s `provider` argument selects the extractor (offline default; the Enterprise Edition adds `llm`/`openai`). Requesting an unregistered provider returns an error. Reranking applies to `search_memory` when `MNEMOVELA_RERANKER` is set to a registered reranker name (EE registers `llm`); unset or `none` preserves the baseline order. These behaviors are inherited via JSON-RPC dispatch. EE LLM providers read `MNEMOVELA_LLM_API_KEY`, `MNEMOVELA_LLM_BASE_URL`, and `MNEMOVELA_LLM_MODEL`.
- `sync_connector` requires the Enterprise Edition. The Go runtime returns a stub; Python dispatches to `service.sync_connector` but effective connector implementations require EE-registered connectors.

## Client configuration

Register the stdio server in an MCP client configuration file (e.g., `mcp.json` or IDE settings):

```json
{
  "mcpServers": {
    "Mneme": {
      "command": "mnemovela-mcp-stdio",
      "env": {
        "Mnemovela_MCP_DATABASE_PATH": "/path/to/mnemovela-mcp.sqlite3"
      }
    }
  }
}
```

For the Go runtime:

```json
{
  "mcpServers": {
    "Mneme-Go": {
      "command": "go",
      "args": ["run", "./cmd/mnemovela-mcp-stdio"],
      "cwd": "/path/to/mnemovela-repo",
      "env": {
        "Mnemovela_GO_PEBBLE_PATH": "/path/to/pebble-dir"
      }
    }
  }
}
```

## See also

- [`./jsonrpc.md`](./jsonrpc.md) -- JSON-RPC API interface
- [`./README.md`](./README.md)
- [`contracts/mnemovela.mcp.v1.schema.json`](../../contracts/mnemovela.mcp.v1.schema.json)
- [`contracts/mnemovela.jsonrpc.v1.schema.json`](../../contracts/mnemovela.jsonrpc.v1.schema.json)
