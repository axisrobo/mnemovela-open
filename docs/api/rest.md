# Mneme REST API

## Overview

The Mneme REST API is a FastAPI service (`services/python-rest-api`) that provides an HTTP/JSON interface over the Mneme OSS memory engine. It is SQLite-backed by default. The service auto-seeds a multilingual demo dataset (Chinese and English) on the first cold start when the database is empty.

**Run locally:**

```
uvicorn mneme_rest_api.main:app --app-dir services/python-rest-api/src --host 0.0.0.0 --port 8000
```

All endpoints are mounted under the base path `/api/v1`. The REST API is a Python application shell over the engine: it routes HTTP requests to the OSS `axisrobo.mnemovela` Python library.

## Endpoint reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | Service health status |
| `GET` | `/api/v1/live` | Liveness check |
| `GET` | `/api/v1/ready` | Readiness check (probes the storage layer) |
| `GET` | `/api/v1/metrics` | Runtime request/error counts and uptime |
| `POST` | `/api/v1/query/search` | Hybrid search over Mneme memory |
| `POST` | `/api/v1/query/timeline` | Chronological timeline query |
| `POST` | `/api/v1/query/context` | Build task context from visible memories |
| `POST` | `/api/v1/query/entity/evolve` | Evolve entity understanding from recent episodes |
| `GET` | `/api/v1/query/connectors/status` | Connector sync status |
| `POST` | `/api/v1/visualizations/graph` | Graph projection for query results |
| `POST` | `/api/v1/jsonrpc` | JSON-RPC 2.0 over HTTP (full Mneme method set) |
| `POST` | `/api/v1/memory/episode` | Add an episode memory |
| `POST` | `/api/v1/memory/fact` | Add a temporal fact |
| `POST` | `/api/v1/memory/commit` | Append a typed memory commit |
| `POST` | `/api/v1/memory/fact/invalidate` | Invalidate an existing fact |
| `POST` | `/api/v1/subjects` | Create or update a subject |
| `POST` | `/api/v1/entities` | Create or update an entity |
| `POST` | `/api/v1/branches` | Create a branch |
| `POST` | `/api/v1/branches/merge` | Merge a source branch into a target branch |
| `POST` | `/api/v1/extract` | Extract derived commits from a stored episode |
| `POST` | `/api/v1/commits/retention` | Set the retention state of a commit |

All endpoints are confirmed present in the router source files:
- `routers/health.py` — `/live`, `/ready`, `/health`, `/metrics`
- `routers/query.py` — `/search`, `/timeline`, `/context`, `/entity/evolve`, `/connectors/status`
- `routers/visualization.py` — `/graph`
- `routers/rpc.py` — `/jsonrpc`
- `routers/write.py` — `/memory/episode`, `/memory/fact`, `/memory/commit`, `/memory/fact/invalidate`, `/subjects`, `/entities`, `/branches`, `/branches/merge`, `/extract`, `/commits/retention`

## Request / response models

### Search

**`SearchRequest`** (`models/query.py:10`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `str \| null` | `null` | Natural-language query string |
| `branch_name` | `str` | `"main"` | Branch to search |
| `snapshot_id` | `str \| null` | `null` | Pinned snapshot ID |
| `subject_scope` | `str \| null` | `null` | Subject scope filter |
| `owner_subject_id` | `str \| null` | `null` | Owner subject filter |
| `participant_subject_ids` | `list[str]` | `[]` | Participant subject IDs |
| `entity_ids` | `list[str]` | `[]` | Entity ID filters |
| `object_ids` | `list[str]` | `[]` | Object ID filters |
| `object_types` | `list[str]` | `[]` | Object type filters |
| `cognitive_profile_id` | `str \| null` | `null` | Cognitive profile ID |
| `memory_types` | `list[str]` | `[]` | Memory type filters |
| `epistemic_status` | `str \| null` | `null` | Epistemic status filter |
| `contradiction_status` | `str \| null` | `null` | Contradiction status filter |
| `retention_states` | `list[str] \| null` | `null` | Retention state filters |
| `modes` | `list[str]` | `["structured","lexical","semantic","relation"]` | Index modes to query |
| `top_k` | `int` | `20` | Number of results to return |
| `candidate_limit` | `int \| null` | `null` | Max candidates per mode |
| `include_explanations` | `bool` | `false` | Include explanation breakdowns |
| `tenant_id` | `str` | `"default"` | Tenant namespace |
| `project_id` | `str` | `"default"` | Project namespace |
| `principal_subject_ids` | `list[str]` | `[]` | Authorization subject IDs |

**`SearchResponse`** — single field `items: list[SearchResultItem]`.

**`SearchResultItem`** — fields: `commit` (`CommitSummary`), `score` (`float`), `matched_modes` (`list[str]`), `explanation` (`SearchExplanationSummary | null`), `frame` (`FrameProjection | null`).

**`CommitSummary`** (`models/common.py:16`) — fields: `commit_id`, `sequence`, `memory_type`, `branch_name`, `created_at`, `retention_state`, `payload`, `metadata`, `frame` (optional `FrameProjection`).

**`SearchExplanationSummary`** — fields: `matched_modes`, `score_breakdown`, `matched_filters`, `reasons`, `lineage`.

### Timeline

**`TimelineRequest`** (`models/query.py:38`) — subset of SearchRequest filters: `branch_name`, `snapshot_id`, `subject_scope`, `owner_subject_id`, `participant_subject_ids`, `entity_ids`, `object_ids`, `object_types`, `memory_types`, `epistemic_status`, `contradiction_status`, `retention_states`, `limit` (default 100), `tenant_id`, `project_id`, `principal_subject_ids`.

**`TimelineResponse`** — single field `items: list[TimelinePoint]`.

**`TimelinePoint`** (`models/common.py:59`) — fields: `commit_id`, `sequence`, `memory_type`, `branch_name`, `created_at`, `label`, `metadata`.

### Context

**`ContextRequest`** (`models/query.py:61`) — fields: `query` (required), `branch_name` (default `"main"`), `budget` (default 1200), `limit` (default 20), `tenant_id`, `project_id`, `principal_subject_ids`.

**`ContextResponse`** — fields: `query`, `budget`, `sections`, `omitted`.

### Entity evolution

**`EntityEvolutionRequest`** (`models/query.py:78`) — fields: `branch_name` (default `"main"`), `min_episodes_before_refresh` (default 3), `limit` (default 50).

**`EntityEvolutionResponse`** — fields: `versions_created`, `entities_reviewed`, `merges_detected`, `audit`.

### Graph

**`GraphRequest`** (`models/visualization.py:9`) — extends `SearchRequest`; overrides `include_explanations` default to `true`.

**`GraphResponse`** — fields: `nodes` (`list[GraphNode]`), `edges` (`list[GraphEdge]`).

**`GraphNode`** — fields: `id`, `label`, `kind`, `metadata`.

**`GraphEdge`** — fields: `source`, `target`, `label`, `kind`, `metadata`.

## Examples

### 1. Hybrid search

```bash
curl -s -X POST http://localhost:8000/api/v1/query/search \
  -H "Content-Type: application/json" \
  -d '{"query": "contract negotiation dispute", "top_k": 3, "include_explanations": true}'
```

The service responds with ranked items:

```json
{
  "items": [
    {
      "commit": {
        "commit_id": "abc123...",
        "sequence": 1,
        "memory_type": "event",
        "branch_name": "main",
        "created_at": "2026-04-06T09:00:00+08:00",
        "retention_state": "active",
        "payload": {
          "title": {"zh": "Xiangmu qidong huiyi wancheng fanwei queren", "en": "Kickoff meeting confirms project scope"}
        },
        "metadata": {}
      },
      "score": 0.87,
      "matched_modes": ["semantic", "structured"],
      "explanation": {
        "matched_modes": ["semantic", "structured"],
        "score_breakdown": {"semantic": 0.62, "structured": 0.25},
        "matched_filters": {},
        "reasons": [],
        "lineage": []
      },
      "frame": null
    }
  ]
}
```

### 2. Build task context

```bash
curl -s -X POST http://localhost:8000/api/v1/query/context \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the status of the contract clause dispute?", "budget": 800, "limit": 10}'
```

### 3. Graph visualization

```bash
curl -s -X POST http://localhost:8000/api/v1/visualizations/graph \
  -H "Content-Type: application/json" \
  -d '{"query": "arbitration threat", "top_k": 15}'
```

The response includes `nodes` and `edges` arrays suitable for rendering:

```json
{
  "nodes": [
    {"id": "commit/abc123", "label": "Xiaoli proposes arbitration", "kind": "commit", "metadata": {}},
    {"id": "clause/contract-a-7", "label": "Contract Clause 7", "kind": "entity", "metadata": {}}
  ],
  "edges": [
    {"source": "commit/abc123", "target": "clause/contract-a-7", "label": "entity_link", "kind": "entity_link", "metadata": {}}
  ]
}
```

## JSON-RPC over HTTP

In addition to the query and write REST routes, the service exposes the full Mneme JSON-RPC method set over HTTP at `POST /api/v1/jsonrpc`. The same endpoint is also served by the Go HTTP server, so a single JSON-RPC-over-HTTP contract works against either runtime.

The request body is a standard JSON-RPC 2.0 request object, and the response is the corresponding JSON-RPC 2.0 response envelope. This transport exposes every `mnemovela.*` method — including `build_context`, the `capture_*` session methods, and the `reconcile_*` maintenance methods — not just the query and write routes described above. JSON-RPC-level failures are returned as a JSON-RPC `error` object with HTTP status `200` (the HTTP layer only reports transport-level problems). See [`./jsonrpc.md`](./jsonrpc.md) for the complete method reference.

```bash
curl -s -X POST http://localhost:8000/api/v1/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "mnemovela.build_context", "params": {"query": "contract dispute status", "branch_name": "main", "budget": 800, "limit": 10}}'
```

The response is a JSON-RPC envelope:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "context_snippet": "...", "sources": ["...", "..."] }
}
```

## Write endpoints

The Python FastAPI service also exposes ten `POST` write routes (`routers/write.py`). These are Python-only; the Go HTTP server offers writes through the JSON-RPC endpoint above.

| Method | Path | Body model | Response | Description |
|--------|------|------------|----------|-------------|
| `POST` | `/api/v1/memory/episode` | `AddEpisodeRequest` (`content` required) | `CommitSummary` | Record a raw episode of agent interaction. |
| `POST` | `/api/v1/memory/fact` | `AddFactRequest` (`fact_id`, `subject_id`, `predicate`, `object_value` required) | `CommitSummary` | Assert a temporal fact about a subject. |
| `POST` | `/api/v1/memory/commit` | `CommitRequest` (`memory_type` required; `payload` object) | `CommitSummary` | Append a typed memory commit. |
| `POST` | `/api/v1/memory/fact/invalidate` | `InvalidateFactRequest` (`fact_id`, `invalidated_at` required) | `CommitSummary` | Mark a fact as invalidated (non-destructive). |
| `POST` | `/api/v1/subjects` | `UpsertSubjectRequest` (`subject_id`, `subject_type` required) | `SubjectSummary` | Create or update a subject. |
| `POST` | `/api/v1/entities` | `UpsertEntityRequest` (`entity_id`, `entity_type` required) | `EntitySummary` | Create or update an entity. |
| `POST` | `/api/v1/branches` | `CreateBranchRequest` (`branch_name` required) | `BranchHeadSummary` | Create a branch, optionally from an existing branch. |
| `POST` | `/api/v1/branches/merge` | `MergeBranchRequest` (`source_branch` required; `strategy` one of `manual`/`ours`/`theirs`) | `CommitSummary` | Merge a source branch into a target branch. |
| `POST` | `/api/v1/extract` | `ExtractEpisodeRequest` (`episode_commit_id` required; `provider` default `offline`) | `ExtractionRun` | Extract derived commits from a stored episode. |
| `POST` | `/api/v1/commits/retention` | `SetRetentionStateRequest` (`commit_id`, `retention_state` required) | `CommitSummary` | Set the retention state of a commit. |

Commit-producing routes return a `CommitSummary` (see the model above); the subject, entity, and branch routes return small summary objects (`SubjectSummary`, `EntitySummary`, `BranchHeadSummary`). The `extract` route's `provider` defaults to `offline` (the deterministic OSS extractor); `llm` and `openai` require the Enterprise Edition.

### Add an episode

```bash
curl -s -X POST http://localhost:8000/api/v1/memory/episode \
  -H "Content-Type: application/json" \
  -d '{"branch_name": "main", "content": "User asked to fix the login form; found a typo in the placeholder.", "episode_type": "conversation", "source": "claude-code"}'
```

### Create a branch

```bash
curl -s -X POST http://localhost:8000/api/v1/branches \
  -H "Content-Type: application/json" \
  -d '{"branch_name": "feature/auth-refactor", "from_branch": "main"}'
```

## Contract status

The OpenAPI contract at `contracts/mnemovela.rest.v1-draft.openapi.json` documents the health, query, and graph endpoints (`/api/v1/health`, `/api/v1/query/search`, `/api/v1/query/timeline`, `/api/v1/visualizations/graph`) and now also covers the JSON-RPC-over-HTTP endpoint (`/api/v1/jsonrpc`) and all ten write endpoints (`/api/v1/memory/episode`, `/api/v1/memory/fact`, `/api/v1/memory/commit`, `/api/v1/memory/fact/invalidate`, `/api/v1/subjects`, `/api/v1/entities`, `/api/v1/branches`, `/api/v1/branches/merge`, `/api/v1/extract`, `/api/v1/commits/retention`). The remaining health/liveness and derived query endpoints (`/live`, `/ready`, `/metrics`, `/query/context`, `/query/entity/evolve`, `/query/connectors/status`) exist in the Python service router source but are not yet described in the v1-draft contract.

## Edition notes

- The `GET /api/v1/query/connectors/status` endpoint lists connector names with a placeholder status (`"available"`, `last_sync: null`, `files_synced: 0`). Actual cloud connector integrations (GitHub, Google Drive, Notion, OneDrive, Feishu, Tencent Docs, S3, Azure Blob) are provided by the Enterprise Edition.

## See also

- [./README.md](./README.md)
- [OpenAPI contract](../../contracts/mnemovela.rest.v1-draft.openapi.json)
