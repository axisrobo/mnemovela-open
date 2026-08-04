# @axisrobo/mnemovela-client (TypeScript)

Thin client for a running Mnemovela server over JSON-RPC/HTTP. Browser + Node 18+, no runtime deps.

```ts
import { MnemeClient } from "@axisrobo/mnemovela-client";

const client = new MnemeClient("http://localhost:8000");
await client.addEpisode({ branch_name: "main", content: "hello" });
const results = await client.searchMemory({ branch_name: "main", query: "hello", top_k: 5 });
```

Points at the server's `POST /api/v1/jsonrpc` endpoint; exposes the full Mnemovela method set.
