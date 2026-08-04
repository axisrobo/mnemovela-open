# Mneme JSON-RPC API

## Overview

Mneme exposes a JSON-RPC 2.0 interface over stdio for local memory operations -- storing subjects, entities, episodes, facts, and commits; querying and searching; running extraction and reconciliation; capturing agent session events; and syncing connectors. The server reads one JSON object per line on stdin and writes one JSON response per line on stdout.

**Launch**

| Runtime | Command | Storage | Env override |
|---------|---------|---------|-------------|
| Go | `go run ./cmd/mnemovela-jsonrpc-stdio` | In-memory (default) or Pebble | `Mnemovela_GO_PEBBLE_PATH` to use Pebble |
| Python | `mnemovela-jsonrpc-stdio` | SQLite | `Mnemovela_JSONRPC_DATABASE_PATH` |

When `Mnemovela_GO_PEBBLE_PATH` is set, the Go runtime switches from in-memory storage to a persistent Pebble database at the given path. The Python runtime always uses a local SQLite database.

**JSON-RPC over HTTP**

In addition to stdio, the same JSON-RPC 2.0 interface is now available over HTTP at `POST /api/v1/jsonrpc`, served by both the Python REST service (`services/python-rest-api`) and the Go HTTP server. The HTTP request body is a single JSON-RPC request object and the response is the matching JSON-RPC response envelope; JSON-RPC-level errors are returned as an `error` object with HTTP status `200`. The HTTP transport exposes the full method set documented below — a superset of the gRPC surface — so any `mnemovela.*` method callable over stdio is also callable over HTTP. See [`./rest.md`](./rest.md) for the REST service details.

## Envelope

Every message conforms to the `mnemovela.jsonrpc.v1` schema (`contracts/mnemovela.jsonrpc.v1.schema.json`).

### Request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "mnemovela.add_episode",
  "params": {
    "branch_name": "main",
    "content": "..."
  }
}
```

`id` may be a string, integer, or `null` (for notifications). All method names use the `mnemovela.` prefix.

### Success response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "...": "..." }
}
```

### Error response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "method not found: mnemovela.unknown"
  }
}
```

Standard JSON-RPC error codes apply (`-32700` parse error, `-32600` invalid request, `-32601` method not found, `-32602` invalid params, `-32000` server error).

## Method reference

The following table lists every `mnemovela.*` method dispatched by either runtime. Methods marked **(Go)** or **(Python)** are available in only one runtime; all others are available in both.

| Method | Required params | Optional params | Description |
|--------|----------------|-----------------|-------------|
| `mnemovela.upsert_subject` | `subject_id`, `subject_type` | `display_name` | Create or update a subject (agent, user, system). |
| `mnemovela.upsert_entity` | `entity_id`, `entity_type` | `canonical_name`, `metadata` | Create or update a knowledge entity. |
| `mnemovela.resolve_entity` | `mention` | `entity_type` | Resolve a text mention to a known entity. |
| `mnemovela.resolve_entity_explained` | `mention` | `entity_type` | Resolve a text mention with explanation output. |
| `mnemovela.add_episode` | `branch_name`, `content` | `episode_type`, `source`, `observed_at`, `metadata`, `owner_subject_id` | Record a raw episode of agent interaction. |
| `mnemovela.commit_memory` | `branch_name`, `memory_type`, `payload` | `owner_subject_id`, `entity_links`, `ontology_assertions`, `visibility_scope` | Commit structured memory (frame, list, hierarchy, etc.). |
| `mnemovela.add_fact` | `branch_name`, `fact_id`, `subject_id`, `predicate`, `object_value` | `valid_from`, `valid_to`, `confidence`, `entity_links` | Assert a temporal fact about a subject. |
| `mnemovela.invalidate_fact` | `branch_name`, `fact_id`, `invalidated_at` | `reason` | Mark a fact as invalidated (non-destructive). |
| `mnemovela.query_facts` | _(none required)_ | `branch_name`, `fact_id`, `subject_id`, `predicate`, `true_at`, `include_invalidated`, `limit` | Query facts with optional filters. |
| `mnemovela.query_memories` | `branch_name` | `entity_ids`, `limit` | List committed memory frames on a branch. |
| `mnemovela.search_memory` | `query` | `branch_name`, `top_k` | Hybrid (keyword + vector) search across memory. |
| `mnemovela.create_branch` | `branch_name` | `from_branch` | Create a new branch, optionally from an existing branch. |
| `mnemovela.merge_branch` | `source_branch` | `target_branch`, `strategy` | Merge one branch into another. |
| `mnemovela.list_branches` **(Python)** | _(none required)_ | `status` | List all branches, optionally filtered by status. |
| `mnemovela.extract_episode` | `branch_name`, `episode_commit_id` | `provider` | Extract frames from a raw episode commit (offline by default). |
| `mnemovela.evolve_entity` | `branch_name` | `min_episodes_before_refresh`, `limit` | Evolve entity representations from recent commits. |
| `mnemovela.build_context` | `query` | `branch_name`, `budget`, `limit` | Build a retrieval-augmented context snippet for a query. |
| `mnemovela.session_start` **(Python)** | `query` | `branch_name`, `budget` | Alias for `build_context` scoped to session start. |
| `mnemovela.get_context` **(Python)** | `query` | `branch_name`, `budget` | Alias for `build_context`. |
| `mnemovela.session_end` | `summary` | `session_id`, `changed_files`, `decisions`, `branch_name` | Capture a session summary and decisions at session end. |
| `mnemovela.capture_tool_call` | `tool_name` | `input_json`, `output_summary`, `branch_name` | Capture a tool invocation from an agent session. |
| `mnemovela.capture_decision` | `decision_summary` | `rationale`, `alternatives`, `branch_name` | Capture a decision made during an agent session. |
| `mnemovela.capture_error` | `error_summary` | `tool_name`, `context`, `branch_name` | Capture an error encountered during an agent session. |
| `mnemovela.capture_constraint` | `constraint_summary` | `scope`, `branch_name` | Capture a constraint or rule for future agent behavior. |
| `mnemovela.reconcile_retention` | `branch_name` | `default_hot_ttl_days`, `default_warm_ttl_days`, `default_cold_ttl_days`, `access_recency_boost_days`, `now` | Apply retention tiering policy to memory. |
| `mnemovela.reconcile_forgetting` | `branch_name` | `min_salience`, `tombstone_grace_days`, `ttl_expiry_enabled`, `contradiction_enabled`, `min_confidence_delta`, `recovery_window_days` | Apply forgetting / contradiction policy to memory. |
| `mnemovela.recover_commit` | `commit_id` | `recovery_window_days` | Recover a soft-deleted commit within the recovery window. |
| `mnemovela.ingest` | `path` | `branch_name` | Ingest a file into memory. Go delegates to Python; Python uses multi-modal ingestion. |
| `mnemovela.sync_connector` | `connector`, `context` | `auth` | Sync files from an external connector. Go delegates to Python. |

**Method counts**: 26 methods dispatched in Go, 29 method-name entries in Python (27 unique dispatch cases; `session_start` and `get_context` alias `build_context`). Python adds `list_branches`, `session_start`, and `get_context`.

## Identity / auth params

The following params are recognized on every method and are used to build an access context (`tenant_id`, `project_id`, `principal_subject_ids`): if not present in the request, the previously-set context values are preserved. Defaults: `tenant_id` = `"default"`, `project_id` = `"default"`, `principal_subject_ids` = `[]`.

## Edition notes

- `extract_episode`'s `provider` parameter selects the extractor. `offline` (the deterministic rule-based extractor) ships in the OSS core and is the default. The Enterprise Edition registers `llm` and `openai`; requesting a provider that is not registered returns a `-32602` error.
- Reranking applies to `search_memory` when `MNEMOVELA_RERANKER` is set to a registered reranker name (EE registers `llm`). Unset or `none` preserves the baseline result order. EE LLM providers read `MNEMOVELA_LLM_API_KEY`, `MNEMOVELA_LLM_BASE_URL`, and `MNEMOVELA_LLM_MODEL`.
- `sync_connector` requires the Enterprise Edition for connector logic. In Go OSS the method returns a stub response noting that connector sync delegates to the Python reference runtime. In Python OSS the method dispatches to `service.sync_connector` but effective connector implementations require EE-registered connectors.

## Examples

### add_episode

Request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "mnemovela.add_episode",
  "params": {
    "branch_name": "main",
    "content": "User asked to fix the login form. I found a typo in the username field's placeholder attribute.",
    "episode_type": "conversation",
    "source": "claude-code"
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "commit_id": "b7a3f1c2-...",
    "frame": { "...": "..." }
  }
}
```

### search_memory

Request:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "mnemovela.search_memory",
  "params": {
    "query": "login form typo",
    "branch_name": "main",
    "top_k": 5
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": [
    {
      "commit_id": "b7a3f1c2-...",
      "score": 0.92,
      "frame": { "...": "..." }
    }
  ]
}
```

### build_context

Request:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "mnemovela.build_context",
  "params": {
    "query": "how do we handle auth tokens",
    "branch_name": "main",
    "budget": 1200,
    "limit": 10
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "context_snippet": "...",
    "sources": [ "...", "..." ]
  }
}
```

## See also

- [`./mcp.md`](./mcp.md) -- MCP (Model Context Protocol) interface
- [`./README.md`](./README.md)
- [`contracts/mnemovela.jsonrpc.v1.schema.json`](../../contracts/mnemovela.jsonrpc.v1.schema.json)
- [`contracts/mnemovela.jsonrpc.v1-draft.schema.json`](../../contracts/mnemovela.jsonrpc.v1-draft.schema.json)
