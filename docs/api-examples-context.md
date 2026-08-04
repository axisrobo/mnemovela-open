# Context Assembly API Examples

## Python

```python
from axisrobo.mnemovela.backends.sqlite import SQLiteMemoryBackend
from axisrobo.mnemovela.engine import LocalMemoryEngine

with LocalMemoryEngine(SQLiteMemoryBackend.in_memory()) as engine:
    context = engine.build_context(query="current project constraints", branch_name="main", budget=1200)
```

## JSON-RPC

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "mnemovela.build_context",
  "params": {
    "query": "current project constraints",
    "branch_name": "main",
    "budget": 1200,
    "tenant_id": "default",
    "project_id": "default",
    "principal_subject_ids": ["agent:opencode"]
  }
}
```
