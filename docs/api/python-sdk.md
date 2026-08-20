# Python SDK Reference

## Overview

The `axisrobo.mnemovela` package is the in-process Python SDK for the Mnemovela memory architecture. It provides local embedded storage (SQLite or in-memory), typed memory commits, hybrid retrieval, entity management, media ingestion, and maintenance orchestration.

**Install** (editable from source):
```bash
pip install -e .
```

**Stable import surfaces:**

```python
from axisrobo.mnemovela import (...)       # top-level aggregated public API
from axisrobo.mnemovela.api import (...)   # direct service/factory entry points
```

Packages such as `_internal/`, `querying/`, `indexing/`, and `management/` are implementation layout and **not** part of the stable consumer API. Backend and index implementors should use `axisrobo.mnemovela.contracts`.

---

## Quick start

### In-memory (ephemeral)

```python
from axisrobo.mnemovela import LocalMemoryService, SQLiteServiceConfig

config = SQLiteServiceConfig(database_path=":memory:", persistent_indexes=False)
with LocalMemoryService.from_sqlite(config) as memory:
    memory.add_episode(branch_name="main", content="Planted an apple tree in the courtyard.")
    memory.add_fact(
        branch_name="main",
        fact_id="fact/apple-tree-location",
        subject_id="entity/apple-tree",
        predicate="located_in",
        object_value="courtyard",
    )
    results = memory.hybrid_search("apple tree", branch_name="main", top_k=5)
    for r in results:
        print(r.score, r.commit.commit_id)

    context = memory.build_context(query="apple tree", branch_name="main", budget=800)
    print(context["summary"])
```

### File-backed SQLite

```python
from axisrobo.mnemovela import LocalMemoryService, SQLiteServiceConfig

config = SQLiteServiceConfig(database_path="./agentic-memory.db", persistent_indexes=True)
with LocalMemoryService.from_sqlite(config) as memory:
    print(memory.branch_head("main"))
```

---

## Service construction

### `LocalMemoryService`

A thin context-manager wrapper over `LocalMemoryEngine`. All engine methods are delegated via `__getattr__`, so you can call any engine method directly on the service.

| Constructor | Description |
|---|---|
| `LocalMemoryService.from_sqlite(config, *, persistent_indexes=None)` | Build from a `SQLiteServiceConfig`, a `str`, or a `Path`. |
| `LocalMemoryService.from_config(config)` | Build from a generic `MemoryServiceConfig` (backend registry lookup). |
| `LocalMemoryService(engine)` | Directly wrap an existing `LocalMemoryEngine`. |

Supports `__enter__`/`__exit__` and explicit `.close()`.

```python
with LocalMemoryService.from_sqlite("./data.db") as memory:
    ...
```

### `MemoryServiceConfig`

A frozen dataclass for backend-agnostic construction. The backend name is resolved against the registered store factories.

```python
from axisrobo.mnemovela import MemoryServiceConfig, create_memory_engine

engine = create_memory_engine(
    MemoryServiceConfig(
        backend="sqlite",       # or "memory"
        settings={"database_path": "./agentic-memory.db"},
        persistent_indexes=True,
    )
)
```

Fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `backend` | `str` | *(required)* | Registered backend name (`"memory"`, `"sqlite"`). |
| `settings` | `dict[str, Any]` | *(required)* | Backend-specific settings dictionary. |
| `persistent_indexes` | `bool` | `True` | Whether to create durable lexical/relation/semantic indexes. |

### `SQLiteServiceConfig` (alias for `SQLiteBackendConfig`)

A frozen dataclass for direct SQLite construction — the simplest path:

```python
from axisrobo.mnemovela import SQLiteServiceConfig, create_sqlite_engine
from axisrobo.mnemovela.backends.sqlite import SQLiteBackendConfig, create_sqlite_engine  # same objects

engine = create_sqlite_engine("./agentic-memory.db", persistent_indexes=True)
```

Fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `database_path` | `str \| Path` | *(required)* | Path to the SQLite file, or `":memory:"`. |
| `persistent_indexes` | `bool` | `True` | Whether to build durable lexical/relation/semantic indexes alongside the database. |

### `create_memory_engine(config)`

Resolves `config.backend` against the store registry and returns a `LocalMemoryEngine`.

```python
create_memory_engine(config: MemoryServiceConfig) -> LocalMemoryEngine
```

### `create_sqlite_engine(config, *, persistent_indexes=None)`

Direct construction of a SQLite-backed `LocalMemoryEngine`. Accepts a `SQLiteBackendConfig`, `str`, or `Path`.

```python
create_sqlite_engine(config: SQLiteBackendConfig | str | Path, *, persistent_indexes: bool | None = None) -> LocalMemoryEngine
```

### Backend registry

The OSS distribution ships two backends:

| Backend name | Description |
|---|---|
| `"memory"` | In-memory storage (ephemeral). |
| `"sqlite"` | SQLite file-backed storage with optional persistent indexes. |

Server backends (e.g. `"postgres"`) are provided by the Enterprise Edition (`axisrobo-mnemovela-ee`). The registry auto-discovers backends at import time so `"postgres"` becomes available without code changes once the EE package is installed.

---

## Writing memory

### Subjects, entities, objects

```python
# Subjects (principals / agents)
memory.upsert_subject(
    *, subject_id, subject_type,
    display_name=None, metadata=None,
) -> SubjectRecord

memory.get_subject(subject_id) -> SubjectRecord | None

# Entities (typed concepts linked to memories)
memory.upsert_entity(
    *, entity_id, entity_type,
    canonical_name=None, metadata=None,
) -> EntityRecord

memory.get_entity(entity_id) -> EntityRecord | None

# Memory objects (typed primary nodes for object-link joins)
memory.upsert_object(
    *, object_id, object_type: MemoryObjectType | str,
    display_name=None, metadata=None,
) -> MemoryObjectRecord

memory.get_object(object_id) -> MemoryObjectRecord | None
```

### Generic `commit`

The low-level commit — all typed helpers resolve to this.

```python
memory.commit(
    *,
    branch_name: str,
    memory_type: MemoryType | str,
    payload: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
    parent_commit_ids: Sequence[str] | None = None,
    subject_scope: SubjectScope | str | None = None,
    epistemic_status: EpistemicStatus | str | None = None,
    owner_subject_id: str | None = None,
    participant_subject_ids: Sequence[str] | None = None,
    subject_links: Sequence[SubjectLink | Mapping[str, Any]] | None = None,
    entity_links: Sequence[EntityLink | Mapping[str, Any]] | None = None,
    object_links: Sequence[MemoryObjectLink | Mapping[str, Any]] | None = None,
    ontology_assertions: Sequence[OntologyAssertion | Mapping[str, Any]] | None = None,
    cognitive_profile_id: str | None = None,
    access_context: AccessContext | None = None,
) -> CommitRecord
```

### `add_episode`

```python
memory.add_episode(
    *,
    branch_name: str,
    content: str,
    episode_type: str = "text",
    source: str | None = None,
    observed_at: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    owner_subject_id: str | None = None,
    entity_links: Sequence[EntityLink | Mapping[str, Any]] | None = None,
    ontology_assertions: Sequence[OntologyAssertion | Mapping[str, Any]] | None = None,
) -> CommitRecord
```

### `add_fact`

```python
memory.add_fact(
    *,
    branch_name: str,
    fact_id: str,
    subject_id: str,
    predicate: str,
    object_value: str,
    valid_from: str | None = None,
    valid_to: str | None = None,
    confidence: float = 1.0,
    metadata: Mapping[str, Any] | None = None,
    entity_links: Sequence[EntityLink | Mapping[str, Any]] | None = None,
) -> CommitRecord
```

### `invalidate_fact`

```python
memory.invalidate_fact(
    *,
    branch_name: str,
    fact_id: str,
    invalidated_at: str,
    reason: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CommitRecord
```

### Typed frame commits

All typed commit helpers share a common signature pattern:

```python
memory.commit_<type>(
    *,
    branch_name: str,
    <frame>: <FrameType> | Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
    parent_commit_ids: Sequence[str] | None = None,
    cognitive_profile_id: str | None = None,
) -> CommitRecord
```

| Method | Frame type | MemoryType |
|---|---|---|
| `commit_event` | `EventFrame` | `EVENT` |
| `commit_knowledge` | `KnowledgeFrame` | `KNOWLEDGE` |
| `commit_experience` | `ExperienceFrame` | `EXPERIENCE` |
| `commit_simulation` | `SimulationFrame` | `SIMULATION` |
| `commit_emotion` | `EmotionFrame` | `EMOTION` |
| `commit_procedure` | `ProcedureFrame` | `PROCEDURE` |
| `commit_intention` | `IntentionFrame` | `INTENTION` |
| `commit_belief` | `BeliefFrame` | `BELIEF` |
| `commit_mission` | `MissionFrame` | `MISSION` |
| `commit_preference` | `PreferenceFrame` | `PREFERENCE` |

All frames accept either a typed dataclass instance or a plain `Mapping[str, Any]` that the engine normalizes internally.

```python
from axisrobo.mnemovela import BeliefFrame, SubjectScope

memory.commit_belief(
    branch_name="main",
    belief=BeliefFrame(
        subject_id="subject/self",
        schema_name="dispute_resolution_prior",
        belief_statements=("evidence-first conversations reduce escalation",),
        bias_tags=("risk-averse",),
        subject_scope=SubjectScope.SELF,
        owner_subject_id="subject/self",
    ),
)
```

---

## Reading / query

### `get_commit`

```python
memory.get_commit(commit_id: str) -> CommitRecord | None
```

### `query_memories`

Deterministic structured filtering over a branch or snapshot.

```python
memory.query_memories(
    *,
    branch_name: str | None = None,
    snapshot_id: str | None = None,
    subject_scope: SubjectScope | str | None = None,
    owner_subject_id: str | None = None,
    participant_subject_ids: Sequence[str] | None = None,
    entity_ids: Sequence[str] | None = None,
    object_ids: Sequence[str] | None = None,
    object_types: Sequence[MemoryObjectType | str] | None = None,
    cognitive_profile_id: str | None = None,
    memory_types: Sequence[MemoryType | str] | None = None,
    epistemic_status: EpistemicStatus | str | None = None,
    contradiction_status: ContradictionStatus | str | None = None,
    retention_states: Sequence[RetentionState | str] | None = None,
    limit: int = 50,
    access_context: AccessContext | None = None,
) -> tuple[CommitRecord, ...]
```

### `hybrid_search`

Ranked hybrid retrieval combining structured, lexical, semantic, and relation recall modes.

```python
memory.hybrid_search(
    query: SearchQuery | str | None = None,
    *,
    modes: Sequence[RecallMode | str] | None = None,
    branch_name: str | None = None,
    snapshot_id: str | None = None,
    subject_scope: SubjectScope | str | None = None,
    owner_subject_id: str | None = None,
    participant_subject_ids: Sequence[str] | None = None,
    entity_ids: Sequence[str] | None = None,
    object_ids: Sequence[str] | None = None,
    object_types: Sequence[MemoryObjectType | str] | None = None,
    cognitive_profile_id: str | None = None,
    memory_types: Sequence[MemoryType | str] | None = None,
    epistemic_status: EpistemicStatus | str | None = None,
    contradiction_status: ContradictionStatus | str | None = None,
    retention_states: Sequence[RetentionState | str] | None = None,
    top_k: int = 20,
    candidate_limit: int | None = None,
    include_explanations: bool = False,
    access_context: AccessContext | None = None,
) -> tuple[SearchResult, ...]
```

Each `SearchResult` has `.commit`, `.score`, `.matched_modes`, and optionally `.explanation` (a `SearchExplanation` with `.reasons`, `.score_breakdown`, `.matched_filters`, `.relation_hits`, `.lineage`).

Default modes (when `modes` is `None`): `STRUCTURED`, `LEXICAL`, `SEMANTIC`, `RELATION`.

### `query_facts`

Walk the fact projection (the most-recent valid fact per `fact_id`) with optional filtering.

```python
memory.query_facts(
    *,
    branch_name: str = "main",
    fact_id: str | None = None,
    subject_id: str | None = None,
    predicate: str | None = None,
    true_at: str | None = None,
    include_invalidated: bool = False,
    limit: int = 50,
    access_context: AccessContext | None = None,
) -> tuple[dict[str, Any], ...]
```

Each returned dict contains keys: `fact_id`, `subject_id`, `predicate`, `object_value`, `confidence`, `valid_from`, `valid_to`, `source_commit_id`, `branch_name`.

### `explain_memory`

Explain why a specific commit matched (or would match) a query.

```python
memory.explain_memory(
    memory_id: str,
    *,
    query: SearchQuery | str | None = None,
    modes: Sequence[RecallMode | str] | None = None,
    branch_name: str | None = None,
    snapshot_id: str | None = None,
    subject_scope: SubjectScope | str | None = None,
    owner_subject_id: str | None = None,
    participant_subject_ids: Sequence[str] | None = None,
    entity_ids: Sequence[str] | None = None,
    object_ids: Sequence[str] | None = None,
    object_types: Sequence[MemoryObjectType | str] | None = None,
    cognitive_profile_id: str | None = None,
    memory_types: Sequence[MemoryType | str] | None = None,
    epistemic_status: EpistemicStatus | str | None = None,
    contradiction_status: ContradictionStatus | str | None = None,
    retention_states: Sequence[RetentionState | str] | None = None,
    top_k: int = 20,
    candidate_limit: int | None = None,
    access_context: AccessContext | None = None,
) -> SearchExplanation
```

### `build_context`

Run `hybrid_search` and assemble a budgeted context dictionary suitable for prompt construction.

```python
memory.build_context(
    *, query: str, branch_name: str = "main", budget: int = 1200, limit: int = 20,
    access_context: AccessContext | None = None,
) -> dict[str, Any]
```

Return shape:

| Key | Type | Description |
|---|---|---|
| `query` | `str` | The original query. |
| `summary` | `str` | Concatenated context text within budget. |
| `sources` | `list[dict]` | Candidate entries with `source_id`, `text`, `section`, `score`, `reason`. |
| `total_budget` | `int` | The budget passed in. |
| `total_used` | `int` | Characters consumed. |

---

## Branches

```python
# Create a standard branch from main (or another source branch)
memory.create_branch(
    branch_name: str, from_branch: str | None = "main",
    metadata: Mapping[str, Any] | None = None,
) -> BranchHead

# Create a TTL-aware simulation branch
memory.create_simulation_branch(
    *, branch_name: str, from_branch: str = "main",
    simulation: SimulationFrame | Mapping[str, Any] | None = None,
    ttl_days: int | None = None,
    cognitive_profile_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BranchHead

# Inspect head of a branch
memory.branch_head(branch_name: str) -> BranchHead | None

# List all branches, optionally filtering by status ("active", "archived")
memory.list_branches(*, status: str | None = None) -> tuple[BranchHead, ...]

# Merge a branch back
memory.merge_branch(
    *, source_branch: str, target_branch: str = "main",
    strategy: str | None = None, metadata: Mapping[str, Any] | None = None,
    cognitive_profile_id: str | None = None,
) -> CommitRecord

# Revert a specific commit
memory.revert_commit(
    *, branch_name: str, commit_id: str,
    metadata: Mapping[str, Any] | None = None,
) -> CommitRecord
```

---

## Entities

```python
# Resolve a mention to an EntityRecord by ID, canonical name, alias, or normalized text
memory.resolve_entity(
    *, mention: str, entity_type: str | None = None,
) -> EntityRecord | None

# Resolve with explanation (returns match_type, matched_value, confidence)
memory.resolve_entity_explained(
    *, mention: str, entity_type: str | None = None,
) -> dict[str, Any]
# Returns: {"entity": EntityRecord|None, "matched": bool, "match_type": str|None,
#           "matched_value": str|None, "confidence": float}

# Evolve entity profiles from accumulated episode evidence
memory.evolve_entity(
    *, branch_name: str = "main", min_episodes_before_refresh: int = 3, limit: int = 50,
) -> dict[str, Any]

# List all registered entities
memory.list_entities() -> tuple[EntityRecord, ...]

# Get version history for an entity
memory.get_entity_versions(entity_id: str, limit: int = 20) -> tuple[...]
```

**Note:** LLM-based entity adjudication (semantic disambiguation, embedding-based matching) requires an LLM client. The Enterprise Edition provides the OpenAI client integration. The OSS core resolution works with `resolve_entity`/`resolve_entity_explained` using rule-based matching (exact ID, canonical name, alias, normalized) and can accept a caller-supplied client through the extraction provider seam.

### `SubjectEntitySearch` (compatibility)

`subject_entity_search(...)` remains available as a historical name that delegates to `query_memories(...)`. New integrations should prefer `query_memories(...)` directly.

---

## Maintenance

### Retention state management

```python
# Set an explicit retention state for a commit
memory.set_retention_state(
    commit_id: str, retention_state: RetentionState | str,
) -> CommitRecord

# Age-based tier reconciliation (advances commits through HOT -> WARM -> COLD -> FROZEN)
memory.reconcile_retention(**kwargs) -> dict[str, Any]

# Reconcile retention states across a branch or snapshot, re-indexing updated commits
memory.reconcile_retention_states(
    *, branch_name: str | None = None, snapshot_id: str | None = None,
) -> tuple[CommitRecord, ...]
```

### Forgetting and recovery

```python
# Execute the forgetting reconciliation pipeline
memory.reconcile_forgetting(**kwargs) -> dict[str, Any]

# Recover a previously tombstoned/forgotten commit
memory.recover_commit(commit_id: str, *, recovery_window_days: int = 90) -> ...
```

### Retention job queue

```python
# Enqueue a retention job
memory.enqueue_retention_job(
    *, action: str, scope_type: str, scope_ref: str | None = None,
    branch_name: str | None = None, payload: Mapping[str, Any] | None = None,
) -> RetentionJobRecord

# List retention jobs, optionally by status
memory.list_retention_jobs(*, status: str | None = None) -> tuple[RetentionJobRecord, ...]

# Run one pending retention job
memory.run_retention_job_once(*, action: str | None = None) -> RetentionJobRecord | None
```

### Snapshots

```python
# Create a named snapshot of the current branch head
memory.create_snapshot(branch_name: str, label: str | None = None) -> SnapshotRecord

# Checkout a snapshot's state (commits up to that point)
memory.checkout_snapshot(snapshot_id: str) -> SnapshotState  # .snapshot, .commits
```

### Tags

```python
# Create a named tag on a branch commit
memory.create_tag(
    *, tag_name: str, branch_name: str, commit_id: str | None = None,
    tag_type: str = "generic", metadata: Mapping[str, Any] | None = None,
) -> TagRecord

# List tags, optionally filtered by branch or commit
memory.list_tags(
    *, branch_name: str | None = None, commit_id: str | None = None,
) -> tuple[TagRecord, ...]
```

### Consistency checks

```python
report = memory.check_consistency(
    *, branch_name: str | None = None, snapshot_id: str | None = None,
) -> ConsistencyReport  # .issue_count, .issues (list of ConsistencyIssue with .kind, .severity, .commit_id, .message)
```

### Contradiction review

```python
# List detected contradictions for a branch
contradictions = memory.list_contradictions(
    *, branch_name: str | None = None, commit_id: str | None = None,
    status: ContradictionStatus | str | None = None,
) -> tuple[ContradictionRecord, ...]

# Open review queue items (active contradictions)
queue = memory.list_review_queue(
    *, branch_name: str | None = None,
    status: ContradictionStatus | str = ContradictionStatus.OPEN,
) -> tuple[ContradictionRecord, ...]

# Progress a contradiction through the review lifecycle
memory.review_contradiction(
    contradiction_id: str,
    *, action: ContradictionReviewAction | str,
    reviewer_id: str | None = None, note: str | None = None,
    resolution: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ContradictionRecord

# List review events (workflow history) for a contradiction
memory.list_contradiction_review_events(contradiction_id: str) -> tuple[ContradictionReviewEvent, ...]
```

### Simulation branch lifecycle

```python
# List simulation branches that have exceeded their TTL
memory.list_expired_simulation_branches(
    *, branch_name: str | None = None,
) -> tuple[BranchHead, ...]

# Archive all expired simulation branches
memory.expire_simulation_branches(
    *, branch_name: str | None = None,
) -> tuple[BranchHead, ...]
```

### Orchestrated maintenance

```python
result = memory.run_maintenance(
    scope: str = "nightly",
    *, branch_name: str | None = None, snapshot_id: str | None = None,
    action: str | None = None, max_jobs: int | None = None,
) -> MaintenanceRunResult  # .scope, .tasks (list of MaintenanceTaskResult), .completed_at
```

Supported scopes: `"media"`, `"retention"`, `"retention-state"`, `"consistency"`, `"index-refresh"`, `"simulation"`, `"nightly"`.

---

## Ingestion and connectors

### `ingest_file`

Ingest a local file, routing it through registered ingestion providers (code, document, diagram, PDF, image, audio, video, archive).

```python
memory.ingest_file(
    path: str, *, branch_name: str = "main",
) -> dict[str, Any]
```

### `ingest_media`

Ingest media references (URIs with metadata) as append-only source commits. Optionally enqueues deferred extraction for transcript, object detection, and event frame derivation.

```python
memory.ingest_media(
    *,
    branch_name: str,
    media_references: Sequence[MediaReference | Mapping[str, Any]],
    metadata: Mapping[str, Any] | None = None,
    enqueue_processing: bool = True,
    extraction_modes: Sequence[MediaExtractionMode | str] | None = None,
    parent_commit_ids: Sequence[str] | None = None,
    subject_scope: SubjectScope | str | None = None,
    epistemic_status: EpistemicStatus | str = EpistemicStatus.OBSERVED,
    owner_subject_id: str | None = None,
    participant_subject_ids: Sequence[str] | None = None,
    subject_links: Sequence[SubjectLink | Mapping[str, Any]] | None = None,
    entity_links: Sequence[Any] | None = None,
    object_links: Sequence[MemoryObjectLink | Mapping[str, Any]] | None = None,
    ontology_assertions: Sequence[OntologyAssertion | Mapping[str, Any]] | None = None,
    cognitive_profile_id: str | None = None,
) -> CommitRecord
```

### Media processing pipeline

```python
# List media references attached to a commit
memory.list_media_references(commit_id: str) -> tuple[MediaReference, ...]

# Enqueue a deferred media extraction job
memory.enqueue_media_processing_job(
    *, source_commit_id: str,
    extraction_modes: Sequence[MediaExtractionMode | str] | None = None,
    payload: Mapping[str, Any] | None = None,
) -> MediaProcessingJobRecord

# List media processing jobs
memory.list_media_processing_jobs(
    *, status: str | None = None, source_commit_id: str | None = None,
) -> tuple[MediaProcessingJobRecord, ...]

# Run one pending media processing job (transcript, object-detection, event-frame)
memory.run_media_processing_job_once() -> MediaProcessingJobRecord | None
```

### `sync_connector`

Synchronize data from a named connector.

```python
memory.sync_connector(
    connector: str, context: str, *, auth: dict[str, str] | None = None,
) -> dict[str, Any]
```

**Important:** Cloud connectors (GitHub, GDrive, OneDrive, Tencent, S3, Azure) ship in the Enterprise Edition (`axisrobo-mnemovela-ee`). In the OSS core alone, `sync_connector` raises `ValueError("Unknown connector: ...")` with a hint to install the EE package. The connector registry auto-discovers connectors at import time when the EE package is present.

---

## Editions note

**OSS Core** (`axisrobo.mnemovela`):

- Embedded backends: `memory` (in-memory), `sqlite` (file-backed with persistent indexes)
- Baseline retrieval: structured filtering, lexical (BM25/term), relation traversal, cosine semantic on local indexes
- Rule-based and offline extraction: `extract_episode` with built-in providers, file ingestion
- Entity resolution: exact-match (ID, canonical name, alias, normalized text)

**Enterprise Edition** (`axisrobo-mnemovela-ee`):

- Additional backends: `postgres` with PGVector
- LLM-powered extraction: OpenAI client for episode-to-fact/frame materialization
- Reranking: LLM-based, graph-based, and neighborhood reranking pipelines
- Full connector suite: GitHub, GDrive, OneDrive, Tencent, S3, Azure
- LLM-based entity adjudication

EE backends and connectors register into the same APIs at import time, so code written against the OSS SDK works unchanged when the EE package is present.

**Activating rerankers and extractors:** `create_memory_engine` honors the `MNEMOVELA_RERANKER` environment variable, setting the engine's reranker from it at construction (unset or `none` preserves the baseline order). `hybrid_search` then applies the selected reranker automatically. Extraction is selected per call via `extract_episode(provider=...)`: `offline` is the default and ships in the OSS core, while the EE registers `llm` and `openai`; requesting an unregistered provider raises a JSON-RPC `-32602` error. EE LLM providers read `MNEMOVELA_LLM_API_KEY`, `MNEMOVELA_LLM_BASE_URL`, and `MNEMOVELA_LLM_MODEL`.

---

## See also

- [API examples](../api-examples.md) — usage patterns for the full Python surface
- [Context assembly examples](../api-examples-context.md) — `build_context` usage
- API hub (`README.md` in this directory) — when available
