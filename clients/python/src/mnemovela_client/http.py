from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any

from mnemovela_client.errors import MnemeError

# Full JSON-RPC method surface exposed as client.<name>(**params).
_RPC_METHODS = (
    "upsert_subject", "upsert_entity", "add_episode", "add_fact", "invalidate_fact",
    "commit_memory", "ingest", "search_memory", "query_memories", "query_facts",
    "build_context", "get_context", "resolve_entity", "resolve_entity_explained",
    "evolve_entity", "extract_episode", "create_branch", "merge_branch", "list_branches",
    "reconcile_retention", "reconcile_forgetting", "recover_commit", "session_start",
    "session_end", "capture_tool_call", "capture_decision", "capture_error",
    "capture_constraint", "sync_connector",
)


class MnemeHttpClient:
    """Synchronous JSON-RPC-over-HTTP client (full method surface, stdlib only)."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self._url = base_url.rstrip("/") + "/api/v1/jsonrpc"
        self._timeout = timeout
        self._id = 0

    def call(self, method: str, **params: Any) -> Any:
        self._id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}).encode("utf-8")
        req = urllib.request.Request(self._url, data=payload, headers={"content-type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise MnemeError(e.code, f"HTTP {e.code}") from e
        if body.get("error"):
            err = body["error"]
            raise MnemeError(err.get("code", -32000), err.get("message", ""), err.get("data"))
        return body.get("result")


class AsyncMnemeHttpClient:
    """Async JSON-RPC-over-HTTP client. Delegates to the sync client in a thread."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self._sync = MnemeHttpClient(base_url, timeout)

    async def call(self, method: str, **params: Any) -> Any:
        return await asyncio.to_thread(self._sync.call, method, **params)


def _attach_methods() -> None:
    def _make_sync(rpc: str):
        def method(self, **params: Any) -> Any:
            return self.call(rpc, **params)
        method.__name__ = name
        return method

    def _make_async(rpc: str):
        async def method(self, **params: Any) -> Any:
            return await self.call(rpc, **params)
        method.__name__ = name
        return method

    for name in _RPC_METHODS:
        rpc = f"mnemovela.{name}"
        setattr(MnemeHttpClient, name, _make_sync(rpc))
        setattr(AsyncMnemeHttpClient, name, _make_async(rpc))


_attach_methods()
