# Go SDK Reference

## Overview

The Mnemovela Go runtime is a zero-dependency, embeddable memory engine that provides CRUD, search, branch-based isolation, fact management, entity resolution, and context assembly. Add it to any Go project:

```bash
go get github.com/axisrobo/mnemovela/go
```

```go
import "github.com/axisrobo/mnemovela/go/core"
```

## Quick start

```go
package main

import (
    "fmt"
    "log"

    "github.com/axisrobo/mnemovela/go/core"
)

func main() {
    rt := core.NewRuntime() // in-memory store, "main" branch auto-created

    // Write
    ep, err := rt.AddEpisode(core.EpisodeInput{
        BranchName:  "main",
        Content:     "The latency of the checkout service dropped from 120ms to 45ms after deploying v2.3.",
        EpisodeType: "text",
        TenantID:    "acme",
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("episode:", ep.CommitID)

    fact, err := rt.AddFact(core.FactInput{
        BranchName:  "main",
        FactID:      "fact-latency-001",
        SubjectID:   "svc/checkout",
        Predicate:   "has_p99_latency_ms",
        ObjectValue: "45",
        Confidence:  0.95,
        TenantID:    "acme",
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("fact:", fact.CommitID)

    // Read
    results, err := rt.SearchMemory("main", "checkout latency", 10)
    if err != nil {
        log.Fatal(err)
    }
    for _, r := range results {
        fmt.Printf("score=%.2f commit=%s\n", r.Score, r.Commit.CommitID)
    }

    // Context assembly
    ctx, err := rt.BuildContext(core.ContextRequest{
        Query:      "checkout latency",
        BranchName: "main",
        Budget:     1200,
        Limit:      10,
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("assembled %d sections within budget %d\n", len(ctx.Sections), ctx.Budget)
}
```

## Runtime construction & backend selection

### Creating a Runtime

```go
rt := core.NewRuntime()                               // in-memory store (volatile)
rt := core.NewRuntimeWithStore(myStore)                // custom Store implementation
```

Both constructors auto-create a `"main"` branch.

### Configuring the backend

```go
store, cleanup, err := core.OpenStoreFromConfig(core.StoreConfigFromEnv())
if err != nil {
    log.Fatal(err)
}
defer cleanup()
rt := core.NewRuntimeWithStore(store)
```

`StoreConfigFromEnv` resolves the backend:

| Env var | Effect |
|---|---|
| `MNEMOVELA_BACKEND` | Select backend by name (e.g. `"pebble"`, `"memory"`) |
| `MNEMOVELA_DATA_PATH` | Data path for the selected backend |
| `Mnemovela_GO_PEBBLE_PATH` | Legacy fallback, sets backend to `"pebble"` |
| _(none set)_ | Defaults to `"memory"` (in-process, volatile) |

### Backend registry

| Method | Signature |
|---|---|
| `RegisterStore(name string, factory StoreFactory)` | Register a backend factory |
| `GetStoreFactory(name string) (StoreFactory, bool)` | Look up a factory |
| `OpenStoreFromConfig(config StoreConfig) (Store, func() error, error)` | Instantiate a store from config |
| `StoreConfigFromEnv() StoreConfig` | Read config from environment |

```go
type StoreConfig struct {
    Name       string
    ConnString string
    Path       string
    Settings   map[string]any
}
```

### Available backends

| Backend | Registration | Description |
|---|---|---|
| `"memory"` | OSS default (init-time registration in `go/core/defaults.go`) | In-process map-based store; no persistence |
| `"pebble"` | OSS: blank-import `"github.com/axisrobo/mnemovela/go/backend/pebble"` | Embedded persistent store using Pebble (CockroachDB's LSM) |
| `"postgres"` | Enterprise Edition (`github.com/axisrobo/mnemovela-ee/go`) | PostgreSQL-backed scalable store |

```go
// Enabling the pebble backend via blank import:
import _ "github.com/axisrobo/mnemovela/go/backend/pebble"
```

## Writing

### CommitMemory

The lowest-level write primitive. All other write helpers delegate to it.

```go
type CommitInput struct {
    BranchName         string              `json:"branch_name"`
    MemoryType         string              `json:"memory_type"`
    Payload            map[string]any      `json:"payload"`
    OwnerSubjectID     string              `json:"owner_subject_id"`
    EntityLinks        []EntityLink        `json:"entity_links"`
    OntologyAssertions []OntologyAssertion `json:"ontology_assertions"`
    Mode               WriteMode           `json:"mode,omitempty"`
    Metadata           map[string]any      `json:"metadata"`
    TenantID           string              `json:"tenant_id"`
    ProjectID          string              `json:"project_id,omitempty"`
    VisibilityScope    VisibilityScope     `json:"visibility_scope,omitempty"`
    ActorSubjectID     string              `json:"actor_subject_id,omitempty"`
    AllowedSubjectIDs  []string            `json:"allowed_subject_ids,omitempty"`
    SessionID          string              `json:"session_id,omitempty"`
    RunID              string              `json:"run_id,omitempty"`
    WorkflowID         string              `json:"workflow_id,omitempty"`
    TaskID             string              `json:"task_id,omitempty"`
}
```

```go
commit, err := rt.CommitMemory(core.CommitInput{
    BranchName: "main",
    MemoryType: "event",
    Payload: map[string]any{
        "event": "deployment",
        "version": "v2.3",
    },
    TenantID: "acme",
})
```

`WriteMode` constants:
- `WriteSync` (`"write_sync"`)
- `WriteAsync` (`"write_async"`)

### AddEpisode

```go
type EpisodeInput struct {
    BranchName     string         `json:"branch_name"`
    Content        string         `json:"content"`
    EpisodeType    string         `json:"episode_type"`
    Source         string         `json:"source"`
    ObservedAt     string         `json:"observed_at"`
    Metadata       map[string]any `json:"metadata"`
    OwnerSubjectID string         `json:"owner_subject_id"`
    Mode           WriteMode      `json:"mode,omitempty"`
    TenantID       string         `json:"tenant_id"`
    ProjectID      string         `json:"project_id,omitempty"`
}
```

```go
ep, err := rt.AddEpisode(core.EpisodeInput{
    BranchName:  "main",
    Content:     "User reported a 500 error on the billing page.",
    EpisodeType: "text",
    TenantID:    "acme",
})
```

Returns the created `Commit`. If `EpisodeType` is empty it defaults to `"text"`.

### AddFact

```go
type FactInput struct {
    BranchName  string         `json:"branch_name"`
    FactID      string         `json:"fact_id"`
    SubjectID   string         `json:"subject_id"`
    Predicate   string         `json:"predicate"`
    ObjectValue string         `json:"object_value"`
    ValidFrom   string         `json:"valid_from"`
    ValidTo     string         `json:"valid_to"`
    Confidence  float64        `json:"confidence"`
    EntityLinks []EntityLink   `json:"entity_links"`
    Mode        WriteMode      `json:"mode,omitempty"`
    Metadata    map[string]any `json:"metadata"`
    TenantID    string         `json:"tenant_id"`
    ProjectID   string         `json:"project_id,omitempty"`
}
```

```go
fact, err := rt.AddFact(core.FactInput{
    BranchName:  "main",
    FactID:      "fact-p99-billing",
    SubjectID:   "svc/billing",
    Predicate:   "has_error_rate",
    ObjectValue: "0.05",
    Confidence:  0.9,
    TenantID:    "acme",
})
```

If `Confidence` is 0 it defaults to `1.0`.

### InvalidateFact

Marks a fact as invalid from a given point in time.

```go
type InvalidateFactInput struct {
    BranchName    string    `json:"branch_name"`
    FactID        string    `json:"fact_id"`
    InvalidatedAt string    `json:"invalidated_at"`
    Reason        string    `json:"reason"`
    Mode          WriteMode `json:"mode,omitempty"`
    TenantID      string    `json:"tenant_id"`
    ProjectID     string    `json:"project_id,omitempty"`
}
```

```go
inv, err := rt.InvalidateFact(core.InvalidateFactInput{
    BranchName:    "main",
    FactID:        "fact-p99-billing",
    InvalidatedAt: "2025-03-15T12:00:00Z",
    Reason:        "error rate corrected after hotfix",
    TenantID:      "acme",
})
```

### SetRetentionState

Sets the retention state of an existing commit (e.g. for tiered storage policies).

```go
commit, err := rt.SetRetentionState("mem_42", "cold")
```

### UpsertSubject / UpsertEntity

```go
subj := rt.UpsertSubject(core.Subject{
    SubjectID:   "user/alice",
    SubjectType: "user",
    DisplayName: "Alice",
    Metadata:    map[string]any{"role": "admin"},
})

ent := rt.UpsertEntity(core.Entity{
    EntityID:      "svc/checkout",
    EntityType:    "service",
    CanonicalName: "Checkout Service",
    Metadata:      map[string]any{"aliases": []string{"checkout", "co"}},
})
```

## Reading

### SearchMemory

Full-text search with hybrid scoring (lexical + optional semantic).

```go
results, err := rt.SearchMemory(branchName, query string, topK int) ([]SearchResult, error)
```

```go
type SearchResult struct {
    Commit       Commit            `json:"commit"`
    Score        float64           `json:"score"`
    MatchedModes []string          `json:"matched_modes"`
    Explanation  SearchExplanation `json:"explanation"`
}
```

When a backend implements `LexicalIndexReader` and the branch is not forked, search uses an inverted-index fast path. When `SemanticIndexReader` is supported and an `Embedder` is set on the runtime, it runs an embedding-based pre-filter. Otherwise it falls back to a full scan.

### QueryMemories

List commits on a branch, optionally filtered by entity links.

```go
commits, err := rt.QueryMemories(branchName string, entityIDs []string, limit int) ([]Commit, error)
```

### QueryFacts

Query the fact projection with temporal and identity filters.

```go
type FactQuery struct {
    BranchName         string `json:"branch_name"`
    FactID             string `json:"fact_id"`
    SubjectID          string `json:"subject_id"`
    Predicate          string `json:"predicate"`
    TrueAt             string `json:"true_at"`
    IncludeInvalidated bool   `json:"include_invalidated"`
    Limit              int    `json:"limit"`
}
```

```go
facts, err := rt.QueryFacts(core.FactQuery{
    BranchName:         "main",
    SubjectID:          "svc/billing",
    TrueAt:             "2025-04-01T00:00:00Z",
    IncludeInvalidated: false,
    Limit:              50,
})
```

If `Limit` is 0 it defaults to 50.

### BuildContext

Assemble a search-context response suitable for injection into LLM prompts.

```go
type ContextRequest struct {
    Query               string   `json:"query"`
    BranchName          string   `json:"branch_name"`
    Budget              int      `json:"budget"`
    Limit               int      `json:"limit"`
    TenantID            string   `json:"tenant_id"`
    ProjectID           string   `json:"project_id"`
    PrincipalSubjectIDs []string `json:"principal_subject_ids"`
}

type ContextResponse struct {
    Query    string           `json:"query"`
    Budget   int              `json:"budget"`
    Sections []ContextSection `json:"sections"`
    Omitted  []ContextOmitted `json:"omitted"`
}

type ContextSection struct {
    Section string        `json:"section"`
    Items   []ContextItem `json:"items"`
}

type ContextItem struct {
    Text     string         `json:"text"`
    SourceID string         `json:"source_id"`
    Reason   string         `json:"reason"`
    Access   map[string]any `json:"access,omitempty"`
}
```

```go
ctx, err := rt.BuildContext(core.ContextRequest{
    Query:  "checkout latency after v2.3",
    Budget: 2000,
    Limit:  20,
})
// Inject ctx into your LLM prompt
```

Default `Budget` is 1200 words; default `Limit` is 20 results. Items are assembled in score order and truncated at budget.

### VerifyCommitIndex

Scans all commit IDs in the store and reports any that are missing from the store.

```go
issues := rt.VerifyCommitIndex()
// Each IndexIssue has CommitID, Kind ("missing"), Detail
```

## Entities & branches

### Entity resolution

| Method | Signature | Description |
|---|---|---|
| `ResolveEntity` | `(mention, entityType string) (Entity, bool)` | Resolve a mention to an entity; matches by entity ID, canonical name, aliases, and normalized text |
| `ResolveEntityExplained` | `(mention, entityType string) map[string]any` | Same resolution but returns a map with `"entity"`, `"matched"`, `"match_type"`, `"matched_value"`, `"confidence"` |
| `ListEntities` | `() []Entity` | List all registered entities |

### Branch management

| Method | Signature | Description |
|---|---|---|
| `CreateBranch` | `(branchName, fromBranch string) (BranchHead, error)` | Fork a new branch from an existing one |
| `MergeBranch` | `(sourceBranch, targetBranch, strategy string) (Commit, error)` | Merge one branch into another; writes a `"merge"` commit on the target branch |
| `ListBranches` | `() []BranchHead` | List all branches |

```go
type BranchHead struct {
    BranchName         string         `json:"branch_name"`
    ParentBranchName   string         `json:"parent_branch_name,omitempty"`
    ForkedFromSequence int            `json:"forked_from_sequence,omitempty"`
    HeadCommitID       string         `json:"head_commit_id,omitempty"`
    HeadSequence       int            `json:"head_sequence"`
    Metadata           map[string]any `json:"metadata"`
}
```

```go
branch, err := rt.CreateBranch("experiment", "main")
// commits to "experiment" are isolated from "main"

mergeCommit, err := rt.MergeBranch("experiment", "main", "squash")
```

## Extension seams

### Store interface

Implement `core.Store` to provide a custom backend:

```go
type Store interface {
    UpsertSubject(subject Subject) error
    UpsertEntity(entity Entity) error
    ListEntities() []Entity
    UpsertEntityVersion(version EntityVersion) error
    UpsertBranch(branch BranchHead) error
    GetBranch(branchName string) (BranchHead, bool)
    ListBranches() []BranchHead
    UpsertCommit(commit Commit) error
    GetCommit(commitID string) (Commit, bool)
    ListCommitIDs() []string
}
```

Optional additional interfaces:
- `TenantFilteredStore` — adds `ListCommitIDsByTenant` / `ListCommitIDsByTenantAndProject`
- `LexicalIndexReader` — enables the fast-path inverted index in `SearchMemory`
- `SemanticIndexReader` — enables embedding-based pre-filtering when an `Embedder` is set
- `FactProjectionReader` — direct fact-history lookups via `FactHistory`
- `FactTimeProjectionReader` — time-indexed fact lookups via `FactsByValidFrom`

### Embedder interface

```go
type Embedder interface {
    Embed(text string) ([]float64, error)
}
```

```go
rt.SetEmbedder(myEmbedder)
```

### Reranker interface

```go
type Reranker interface {
    Rerank(query string, passages []string) []float64
}
```

Registered with `RegisterReranker(name, factory)`. Lookup via `GetRerankerFactory(name)`.

```go
type RerankerConfig struct {
    Provider string
    APIKey   string
    BaseURL  string
    Model    string
}
```

OSS default: `"none"` (no-op reranker, returns all-zero scores).

The active reranker is set via `Runtime.SetReranker(...)` and applied inside `SearchMemory`. The command binaries call `core.SetReranker(core.RerankerFromEnv())` at startup, where `RerankerFromEnv()` reads the `MNEMOVELA_RERANKER` environment variable (unset or `none` leaves the baseline ordering unchanged). The EE registers `llm` as a `Reranker`; its graph/neighborhood capabilities are EE utilities and are not auto-applied rerankers.

### ExtractionProvider interface

```go
type ExtractionProvider interface {
    ProviderID() string
    Extract(episode Commit) (ExtractionResult, error)
}
```

Registered with `RegisterExtractor(name, factory)`. Lookup via `GetExtractorFactory(name)`.

The extractor is selected by the `extract_episode` `provider` parameter (default `offline`, which ships in the OSS core). The EE registers `llm` and `openai`; requesting a provider that is not registered returns an error. EE LLM providers read `MNEMOVELA_LLM_API_KEY`, `MNEMOVELA_LLM_BASE_URL`, and `MNEMOVELA_LLM_MODEL`.

```go
type ExtractorConfig struct {
    Provider string
    APIKey   string
    BaseURL  string
    Model    string
}
```

OSS default: `"offline"` (deterministic parser that reads an `"extraction"` block from the episode payload).

Call `rt.ExtractEpisode(branchName, episodeCommitID, provider)` to run a provider against an episode. The method is idempotent by fingerprint and re-uses prior extraction runs.

### LLMClient interface

```go
type LLMClient interface {
    CompleteStructured(prompt string) (string, error)
    Embed(text string) ([]float64, error)
}
```

`StripCodeFences(text string) string` removes Markdown code fences from LLM responses so the inner JSON can be parsed.

### Authorization

Set an `Authorizer` on the runtime to enforce tenant/project isolation and subject-level visibility:

```go
type Authorizer interface {
    CanAccess(req AccessRequest) AccessDecision
}
```

```go
rt.SetAuthorizer(core.DefaultAuthorizer{})
rt.SetAuthorizationContext(core.AuthorizationContext{
    TenantID:            "acme",
    ProjectID:           "billing",
    PrincipalSubjectIDs: []string{"user/alice"},
})
```

`VisibilityScope` constants: `VisibilityPrivate`, `VisibilitySharedSubjects`, `VisibilityProject`, `VisibilityTenant`, `VisibilityGlobal`.

### Event bus

```go
eventBus := rt.EventBus()
// core.EventBus interface: Subscribe, SubscribeAsync, Publish, Close
```

Event types: `EventCommitStored`, `EventEntityUpserted`, `EventFactStored`, `EventFactInvalidated`, `EventEpisodeStored`, `EventExtractionQueued`, `EventExtractionComplete`, `EventBranchCreated`, `EventBranchMerged`.

### Enterprise Edition

The Enterprise Edition module (`github.com/axisrobo/mnemovela-ee/go`) provides additional registrations that are not in OSS:

| Category | OSS defaults | EE additions |
|---|---|---|
| Store backends | `memory`, `pebble` | `postgres` |
| Extractors | `offline` | `llm`, `openai` |
| Rerankers | `none` | `llm` |
| Utilities | — | Graph topology, neighborhood expansion, cognitive enrichment |

## Command-line binaries

| Binary | Source | Description | Key env vars |
|---|---|---|---|
| `mnemovela-jsonrpc-stdio` | `go/cmd/mnemovela-jsonrpc-stdio` | JSON-RPC 2.0 over stdin/stdout | `MNEMOVELA_BACKEND`, `MNEMOVELA_DATA_PATH`, `Mnemovela_GO_PEBBLE_PATH` |
| `mnemovela-mcp-stdio` | `go/cmd/mnemovela-mcp-stdio` | Model Context Protocol (MCP) over stdin/stdout | `MNEMOVELA_BACKEND`, `MNEMOVELA_DATA_PATH`, `Mnemovela_GO_PEBBLE_PATH` |
| `mnemovela-http` | `go/cmd/mnemovela-http` | JSON-RPC HTTP server | `Mnemovela_HTTP_ADDR` (default `127.0.0.1:8080`) |
| `mnemovela-grpc` | `go/cmd/mnemovela-grpc` | gRPC server with health check | `Mnemovela_GRPC_PORT` (default `9090`) |

All binaries use `StoreConfigFromEnv()` for backend selection and blank-import the pebble backend.

## Parity note

The Go core (`go/core`) covers **CRUD, search, context assembly, branching, retention state, fact temporal projection, entity resolution, and authorization**. Typed frame helpers and media ingestion capabilities reside in the Python SDK. Advanced algorithms (LLM-powered extraction, graph topology, neighborhood expansion, cognitive enrichment) are provided by the Enterprise Edition.

## See also

- [API & SDK hub](README.md) — choose another surface
- [`./jsonrpc.md`](./jsonrpc.md) — JSON-RPC 2.0 API reference
- [`./mcp.md`](./mcp.md) — Model Context Protocol reference
