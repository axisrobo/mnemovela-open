# Mnemovela Python Client

`mnemovela-client` is a thin sync + async Python gRPC client for the
[Mnemovela](https://github.com/axisrobo/mnemovela) cognition runtime. It ships
self-contained gRPC stubs generated from `contracts/mnemovela.v1.proto`
(`service mnemovela.v1.Mnemovela`, 17 RPCs) and wraps them with an ergonomic surface
that returns plain dicts.

Published to `Mnemovela-open` under Apache-2.0.

## Install

```powershell
py -3.13 -m pip install mnemovela-client
```

From a source checkout (with dev tooling to regenerate stubs):

```powershell
py -3.13 -m pip install -e "clients/python[dev]"
```

## Quickstart

Connect to a running Mnemovela gRPC server (default `localhost:9090`), write an
episode, and search memory:

```python
from mnemovela_client import MnemeClient

with MnemeClient("localhost:9090") as client:
    commit = client.add_episode(branch_name="main", content="shipped the client")
    print(commit["commit_id"])

    results = client.search_memory("main", "client", top_k=5)
    for r in results:
        print(r["score"], r["commit"]["commit_id"])
```

Async usage mirrors the sync surface:

```python
import asyncio
from mnemovela_client import AsyncMnemeClient

async def main():
    client = AsyncMnemeClient("localhost:9090")
    commit = await client.add_episode(branch_name="main", content="async hello")
    print(commit["commit_id"])
    await client.close()

asyncio.run(main())
```

## Surface

The client exposes one method per gRPC RPC. The full surface is the 17
`mnemovela.v1.Mnemovela` RPCs: `commit_memory`, `add_episode`, `add_fact`,
`invalidate_fact`, `upsert_subject`, `upsert_entity`, `search_memory`,
`query_memories`, `query_facts`, `resolve_entity`, `resolve_entity_explained`,
`extract_episode`, `create_branch`, `merge_branch`, `list_branches`,
`set_retention_state`, and `verify_commit_index`. Other operations arrive via
future transports (REST, JSON-RPC).

## HTTP transport

Alongside the gRPC client, `MnemeHttpClient` (sync) and `AsyncMnemeHttpClient`
(async) speak JSON-RPC over HTTP (`POST /api/v1/jsonrpc`). They are stdlib-only
(no extra dependencies) and expose the FULL ~29-method surface — including
operations not on the typed gRPC client, such as `build_context`, `get_context`,
`ingest`, `evolve_entity`, and the `capture_*`/`session_*` methods. Each method
is called as `client.<name>(**params)` and returns the JSON-RPC `result`.

```python
from mnemovela_client import MnemeHttpClient

client = MnemeHttpClient("http://localhost:8000")
commit = client.add_episode(branch_name="main", content="shipped the client")
print(commit["commit_id"])

context = client.build_context(branch_name="main", query="client")
client.capture_decision(branch_name="main", summary="use JSON-RPC transport")
```

Async usage mirrors the sync surface:

```python
import asyncio
from mnemovela_client import AsyncMnemeHttpClient

async def main():
    client = AsyncMnemeHttpClient("http://localhost:8000")
    results = await client.search_memory(branch_name="main", query="client", top_k=5)
    print(len(results))

asyncio.run(main())
```

The gRPC `MnemeClient`/`AsyncMnemeClient` remain for the typed 17-RPC surface.

## Regenerating stubs

The generated stubs under `src/mnemovela_client/_generated/` are committed. To
regenerate them from the shared contract:

```powershell
py -3.13 -m pip install grpcio grpcio-tools protobuf
py -3.13 scripts/gen_stubs.py
```
