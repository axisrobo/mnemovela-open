# Mnemovela-open

Open (Apache-2.0) client SDKs, examples, API reference, and prebuilt binaries
for **[Mnemovela](https://github.com/axisrobo/mnemovela)**.

## What is Mnemovela?

Mnemovela is a **cognition runtime** that gives software agents long-term memory,
context assembly, and knowledge representation. Think of it as a memory
subsystem that sits alongside your LLM: every observation, fact, decision, and
plan is stored as a typed, temporal, branchable record, and you retrieve it with
a hybrid search (lexical + semantic + relation + time) plus context assembly.

Mnemovela's data model combines Git-like branching with cognitive memory types:

| Memory type | Example |
|-------------|---------|
| **episode** | raw events (user said X, server returned Y) |
| **fact** | asserted truths (subject-predicate-object, with validity windows) |
| **knowledge** | structured belief (entity relationships, classifications) |
| **experience** | reflection after an action ("what went well / poorly") |
| **simulation** | hypothetical scenarios run to reason about outcomes |
| **emotion**, **intention**, **procedure**, **belief**, **mission**, **preference** | internal agent state |

Every record is **immutable and append-only**, tagged with branch, timestamp,
retention tier, and identity scope (tenant/project). The engine owns the
semantics; storage backends are replaceable.

## What is Mnemovela-open?

**Mnemovela-open** is the public, open-source window into Mnemovela. It contains
everything you need to **integrate with a running Mnemovela server** — client
libraries, CLI tools, protocol schemas, and API documentation —?under the
**Apache-2.0** license. The Mnemovela engine source is not included here; this
repository ships only the client-facing layer.

**What's in this repository:**

| Directory | Contents |
|-----------|----------|
| `clients/` | Thin network clients in four languages (Python, TypeScript, Go, plus CLI tools in Python and Go) |
| `examples/` | Runnable quickstarts that exercise the clients against a live server |
| `docs/` | Full API reference (Python SDK, Go SDK, JSON-RPC, MCP, REST, gRPC) |
| `contracts/` | Language-neutral protocol schemas (JSON-RPC, MCP, REST/OpenAPI, gRPC Proto) |

**What's NOT here (in the private Mnemovela engine repo):**
the engine server + storage backends + advanced algorithms (LLM reranking,
LLM extraction, graph/neighborhood expansion, cloud connectors, contradiction
detection, simulation). Prebuilt binaries of the engine servers ARE available
from this repository's releases.

## Getting started

1. **Get a server binary.** Download a prebuilt server binary from the [latest
   GitHub release](https://github.com/axisrobo/mnemovela-open/releases) for your platform.
   (See [local build](#building-from-source) if you prefer to build from the
   engine source.)
2. **Start the server:**
   ```bash
   mnemovela-http   # JSON-RPC over HTTP + REST, default 127.0.0.1:8080
   mnemovela-grpc   # gRPC, default :9090
   ```
   The server starts with an in-memory backend. Set `Mnemovela_GO_PEBBLE_PATH` for
   pebble persistence.
3. **Pick a client and integrate:**

   **Python (gRPC + HTTP):**
   ```bash
   pip install ./clients/python
   ```
   ```python
   from mnemovela_client import MnemeClient  # gRPC
   from mnemovela_client import MnemeHttpClient  # HTTP (full method surface)
   client = MnemeHttpClient("http://127.0.0.1:8080")
   client.add_episode(branch_name="main", content="hello")
   client.search_memory(branch_name="main", query="hello")
   ```

   **Go (gRPC + HTTP):**
   ```go
   import "github.com/axisrobo/mnemovela-open/clients/go/mnemovela"
   t := mnemovela.NewJSONRPCTransport("http://localhost:8080")
   c := mnemovela.New(t)
   raw, _ := c.AddEpisode(ctx, mnemovela.P{"branch_name":"main","content":"hi"})
   ```

   **TypeScript (HTTP):**
   ```typescript
   import { MnemeClient } from "@axisrobo/mnemovela-client";
   const client = new MnemeClient("http://127.0.0.1:8080");
   await client.addEpisode({ branch_name: "main", content: "hello" });
   ```

   **CLI:**
   ```bash
   mnemovela --transport http add-episode --branch main --content "hi"
   mnemovela search --branch main --query "hi"
   ```

   See `docs/api/` for the full API reference, and `examples/` for runnable
   quickstarts.

## How the clients talk to the server

All clients speak one of three protocols, all implemented by the same server
binary:

| Protocol | Best for | Endpoint | Client support |
|----------|----------|----------|----------------|
| **JSON-RPC over HTTP** | full method set (~29 operations incl. `build_context`, `capture_*`) | `POST /api/v1/jsonrpc` | Python HTTP, TypeScript, Go HTTP, CLI |
| **gRPC** | typed, strongly-consistent surface (17 RPCs) | `:9090` | Python gRPC, Go gRPC, CLI |
| **REST** | dashboard/web UI usage | `GET/POST /api/v1/...` | any HTTP client |

## License

Source content is **Apache-2.0** (`LICENSE`). Prebuilt binaries are distributed
under separate terms (`BINARY-LICENSE.md`). The Mnemovela engine (not in this
repository) is licensed separately.

## Building from source

The server binaries in the releases are built from the Mnemovela engine source. If
you have access to the engine repository, build them with:
```bash
cd go && CGO_ENABLED=0 go build ./cmd/mnemovela-http ./cmd/mnemovela-grpc ./cmd/mnemovela-jsonrpc-stdio ./cmd/mnemovela-mcp-stdio
```
