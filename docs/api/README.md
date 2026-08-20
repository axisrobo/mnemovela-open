# Mnemovela API & SDK Reference

This is the reference hub for every way to talk to Mnemovela. Mnemovela exposes one
semantic memory contract through several surfaces; pick the surface that matches
how you deploy.

## Choose a surface

| Surface | Best for | Language | Reference |
|---------|----------|----------|-----------|
| **Python SDK** | Embedding Mnemovela in a Python app/notebook; the most complete surface (typed frames, ingestion, maintenance) | Python | [python-sdk.md](python-sdk.md) |
| **Go SDK** | Embedding a zero-dependency runtime in a Go agent/service | Go | [go-sdk.md](go-sdk.md) |
| **JSON-RPC** | Language-neutral, network/stdio integration | any | [jsonrpc.md](jsonrpc.md) |
| **MCP** | Exposing memory tools to LLM agents / IDEs | any (MCP client) | [mcp.md](mcp.md) |
| **REST** | Dashboards, web UIs, HTTP clients | any (HTTP) | [rest.md](rest.md) |
| **gRPC** | Strongly-typed, high-throughput services | any (gRPC) | [grpc.md](grpc.md) |

If you are unsure, start with the **Python SDK** (richest and best-documented)
or **JSON-RPC** (simplest cross-language contract).

## One contract, many surfaces

Every surface maps onto the same core operations: write typed memory (episodes,
facts, and fourteen cognitive frame types), retrieve via hybrid search, assemble
task context, resolve/evolve entities, and manage Git-like branches, retention,
and forgetting. The JSON-RPC method names (`mnemovela.*`), the MCP tool names, the
REST routes, and the gRPC RPCs all correspond to the same engine methods
documented in the Python and Go SDK references.

The authoritative machine-readable definitions live in
[`../../contracts/`](../../contracts):

| Contract | Surface |
|----------|---------|
| `mnemovela.jsonrpc.v1.schema.json` | JSON-RPC envelope + methods |
| `mnemovela.mcp.v1.schema.json` | MCP tools |
| `mnemovela.rest.v1-draft.openapi.json` | REST (OpenAPI 3.1) |
| `mnemovela.v1.proto` | gRPC service |
| `mnemovela.memory_frames.v1.schema.json` | The fourteen typed memory frames |
| `mnemovela.memory.v1.schema.json` | Memory-operation semantics (shared fixtures) |
| `mnemovela.context.v1.schema.json` | `build_context` response (ContextBundle v1) |
| `mnemovela.event.v1-draft.schema.json` | Event envelope |

Contracts tagged `v1` are frozen; `v1-draft` contracts are still evolving.

## Editions

Mnemovela is open core. Every surface above ships in the **open-source core**
(AGPL-3.0), but some operations depend on implementations provided by the
proprietary **Enterprise Edition** (`axisrobo-mnemovela-ee`), which registers into
the same APIs at startup:

| Capability reachable through the APIs | OSS core | Enterprise Edition |
|---------------------------------------|----------|--------------------|
| Storage backends | SQLite, Pebble, in-memory | PostgreSQL/PGVector, other server backends |
| Retrieval reranking | `none` (baseline scoring) | LLM rerank, graph rerank, neighborhood expansion |
| Extraction (`extract_episode`) | `offline` (rule-based) | `llm` / `openai` (LLM-backed) |
| Cloud connectors (`sync_connector`) | none | GitHub, Google Drive, OneDrive, Tencent Docs, S3, Azure Blob |

When the Enterprise Edition is not installed, the core still exposes these
methods, but they use the embedded/baseline defaults (and `sync_connector`
returns an "unknown connector" error until connectors are registered). Each
surface reference calls out the EE-dependent operations.

### Activating Enterprise implementations

EE rerankers and extractors register into the same APIs at startup and are now
invoked automatically once selected:

- **Reranking:** set `MNEMOVELA_RERANKER` to a registered reranker name to apply it
  to `search_memory`. Unset or `none` keeps the baseline ordering. The EE
  registers `llm` (its `graph`/`neighborhood` capabilities are EE utilities, not
  auto-applied `Reranker`s).
- **Extraction:** the `extract_episode` `provider` parameter selects the
  extractor. `offline` (rule-based) ships in the OSS core; the EE adds `llm` and
  `openai`. Requesting an unregistered provider returns an error.
- **LLM credentials:** EE LLM providers read `MNEMOVELA_LLM_API_KEY`,
  `MNEMOVELA_LLM_BASE_URL`, and `MNEMOVELA_LLM_MODEL`.

With none of these set, behavior is identical to the OSS baseline (the no-op
reranker is never applied and `offline` is the default extractor).

## Also see

- [../api-examples.md](../api-examples.md) - worked Python usage examples
- [../api-examples-context.md](../api-examples-context.md) - context-assembly examples
