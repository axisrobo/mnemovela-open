# Mneme gRPC API

## Overview

The Mneme gRPC service is defined by the Protocol Buffers contract `contracts/mnemovela.v1.proto`. A production-ready Go server (`go/server/grpc`) implements the full surface and registers health checking via `grpc.health.v1`.

**Run locally:**

```
go run ./cmd/mnemovela-grpc
```

The server listens on the port specified by the environment variable `Mnemovela_GRPC_PORT` (default `9090`). An embedded Pebble store backs the runtime by default.

All RPCs belong to the `mnemovela.v1.Mneme` service.

## Service & RPCs

### Typed writes

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `CommitMemory` | `CommitMemoryRequest` | `CommitMemoryResponse` | Commit a memory to a branch |
| `AddEpisode` | `AddEpisodeRequest` | `AddEpisodeResponse` | Add a raw episode |
| `AddFact` | `AddFactRequest` | `AddFactResponse` | Insert a temporal fact |
| `InvalidateFact` | `InvalidateFactRequest` | `InvalidateFactResponse` | Invalidate a fact |
| `UpsertSubject` | `UpsertSubjectRequest` | `UpsertSubjectResponse` | Create or update a subject |
| `UpsertEntity` | `UpsertEntityRequest` | `UpsertEntityResponse` | Create or update an entity |

### Queries

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `SearchMemory` | `SearchMemoryRequest` | `SearchMemoryResponse` | Hybrid search across indexed memories |
| `QueryMemories` | `QueryMemoriesRequest` | `QueryMemoriesResponse` | Direct commit lookup by branch and entity filters |
| `QueryFacts` | `QueryFactsRequest` | `QueryFactsResponse` | Query facts by subject, predicate, or temporal bounds |

### Resolution

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `ResolveEntity` | `ResolveEntityRequest` | `ResolveEntityResponse` | Resolve a mention to a known entity |
| `ResolveEntityExplained` | `ResolveEntityExplainedRequest` | `ResolveEntityExplainedResponse` | Resolve with match metadata and confidence |

### Extraction (Phase 2)

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `ExtractEpisode` | `ExtractEpisodeRequest` | `ExtractEpisodeResponse` | Run extraction on an episode commit |

### Branching

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `CreateBranch` | `CreateBranchRequest` | `CreateBranchResponse` | Create a new branch |
| `MergeBranch` | `MergeBranchRequest` | `MergeBranchResponse` | Merge source branch into target |
| `ListBranches` | `ListBranchesRequest` | `ListBranchesResponse` | List all branches |

### Maintenance (Phase 2)

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `SetRetentionState` | `SetRetentionStateRequest` | `SetRetentionStateResponse` | Change retention state of a commit |
| `VerifyCommitIndex` | `VerifyCommitIndexRequest` | `VerifyCommitIndexResponse` | Verify index consistency for a commit |

All 17 RPCs are confirmed present in `contracts/mnemovela.v1.proto` and implemented by the Go server at `go/server/grpc/server.go`.

## Messages

### Shared types

**`Commit`** — the core domain object returned by write and query methods. Fields: `sequence` (int32), `commit_id` (string), `branch_name` (string), `memory_type` (string), `retention_state` (string), `created_at` (string), `tenant_id` (string), `payload` (map<string, Value>), `metadata` (map<string, Value>), `parent_commit_ids` (repeated string), `entity_links` (repeated `EntityLink`), `ontology_assertions` (repeated `OntologyAssertion`), `owner_subject_id` (string), `project_id` (string).

**`EntityLink`** — `entity_id`, `entity_role`, `confidence`.

**`OntologyAssertion`** — `entity_id`, `predicate`, `object_value`, `confidence`.

**`Value`** — a `oneof` wrapper mimicking `google.protobuf.Value` for arbitrary JSON: `string_value`, `number_value`, `bool_value`, `struct_value`, `list_value`.

### Key request/response messages

**`CommitMemoryRequest`** — requires `branch_name`, `memory_type`, `payload`, `metadata` maps, and optional `owner_subject_id`, `tenant_id`, `project_id`, `entity_links`, `ontology_assertions`, `principal_subject_ids`, `session_id`.

**`SearchMemoryRequest`** — `branch_name`, `query`, `top_k` (int32), `entity_ids` (repeated), `tenant_id`, `project_id`, `principal_subject_ids`.

**`SearchMemoryResponse`** — `results` (repeated `SearchResult`, each with `commit`, `score`, `matched_modes`).

**`QueryMemoriesRequest`** — `branch_name`, `entity_ids`, `limit`, `tenant_id`, `project_id`, `principal_subject_ids`.

**`QueryFactsRequest`** — `branch_name`, `fact_id` (optional), `subject_id` (optional), `predicate` (optional), `true_at` (temporal point), `include_invalidated`, `limit`, plus tenant/project IDs.

**`QueryFactsResponse`** — `facts` (repeated `FactItem`: `fact_id`, `subject_id`, `predicate`, `object_value`, `confidence`, `valid_from`, `valid_to`, `source_commit_id`, `branch_name`).

**`ResolveEntityRequest`** — `mention`, `entity_type`, `tenant_id`, `project_id`, `principal_subject_ids`.

**`CreateBranchRequest`** — `branch_name`, `from_branch`, `tenant_id`, `project_id`, `principal_subject_ids`.

**`MergeBranchRequest`** — `source_branch`, `target_branch`, `strategy`, `tenant_id`, `project_id`, `principal_subject_ids`.

**`ListBranchesResponse`** — `branches` (repeated `Branch`: `branch_name`, `parent_branch_name`, `head_sequence`, `head_commit_id`).

**`SetRetentionStateRequest`** — `commit_id`, `retention_state`, `tenant_id`, `project_id`, `principal_subject_ids`.

**`VerifyCommitIndexResponse`** — `issues` (repeated `IndexIssue`: `commit_id`, `kind`, `detail`).

## Example

### SearchMemory with grpcurl

Assuming the service is running on `localhost:9090`:

```bash
grpcurl -plaintext \
  -d '{"branch_name":"main","query":"contract clause ambiguity","top_k":5}' \
  localhost:9090 mnemovela.v1.Mneme/SearchMemory
```

### SearchMemory with Go client

```go
import (
    "context"
    Mnemovelav1 "github.com/axisrobo/mnemovela/go/api/mnemovela/v1"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
)

conn, _ := grpc.Dial("localhost:9090", grpc.WithTransportCredentials(insecure.NewCredentials()))
defer conn.Close()

client := Mnemovelav1.NewMnemeClient(conn)
resp, err := client.SearchMemory(context.Background(), &Mnemovelav1.SearchMemoryRequest{
    BranchName: "main",
    Query:      "contract clause ambiguity",
    TopK:       5,
})
```

## Notes

- The `contracts/mnemovela.v1.proto` file is the authoritative `v1` contract.
- Generated Go stubs live in `go/api/mnemovela/v1/` (`mnemovela.pb.go`, `mnemovela_grpc.pb.go`).
- Health checking is available via the standard `grpc.health.v1.Health/Check` service.

## See also

- [./README.md](./README.md)
- [go-sdk.md](./go-sdk.md)
- [Proto contract](../../contracts/mnemovela.v1.proto)
