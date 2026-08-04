# API Examples

## Scope

This document explains the current Python integration surface of the Mneme architecture in terms of package layering.

Use these rules first:

- application code should prefer the top-level `axisrobo.mnemovela` package and `axisrobo.mnemovela.api`
- the top-level package exports are aggregated through `axisrobo.mnemovela.public_api`, but normal consumers should still import from `axisrobo.mnemovela`
- backend or index implementors may depend on `axisrobo.mnemovela.contracts`
- `axisrobo.mnemovela.errors` remains a stable compatibility path, while the canonical implementation now lives under `axisrobo.mnemovela.core`
- grouped packages such as `querying/`, `indexing/`, `management/`, and `_internal/` are implementation layout, not the preferred integration surface for normal consumers

## Layering Summary

### For applications

Prefer:

- `from axisrobo.mnemovela import ...`
- `from axisrobo.mnemovela.api import ...`

These are the stable public entry points.

If you are maintaining older compatibility imports, use explicit compat submodules such as `axisrobo.mnemovela.compat.sqlite`, `axisrobo.mnemovela.compat.querying`, or `axisrobo.mnemovela.compat.management`.

### For backend and index implementors

Prefer:

- `from axisrobo.mnemovela.contracts import StorageBackend`
- `from axisrobo.mnemovela.contracts import RelationIndex, SemanticIndex, LexicalIndex`

These are the stable abstract contracts for extension work.

### For internal contributors

The real implementation is grouped by domain:

- `axisrobo.mnemovela.ingestion`
- `axisrobo.mnemovela.querying`
- `axisrobo.mnemovela.indexing`
- `axisrobo.mnemovela.management`
- `axisrobo.mnemovela.jobs`
- `axisrobo.mnemovela.backends`
- `axisrobo.mnemovela._internal`

Do not treat `_internal` as a stable consumer API.

## Create a Service

The simplest application entry point is still the service wrapper.

```python
from axisrobo.mnemovela import LocalMemoryService, SQLiteServiceConfig

config = SQLiteServiceConfig(database_path="./agentic-memory.db", persistent_indexes=True)

with LocalMemoryService.from_sqlite(config) as memory:
    print(memory.branch_head("main"))
```

If you want backend-agnostic construction, use the API-layer factory path.

```python
from axisrobo.mnemovela import MemoryServiceConfig, create_memory_engine

engine = create_memory_engine(
    MemoryServiceConfig(
        backend="sqlite",
        settings={"database_path": "./agentic-memory.db"},
        persistent_indexes=True,
    )
)
try:
    print(engine.branch_head("main"))
finally:
    engine.close()
```

## Register Subjects, Entities, and Objects

```python
from axisrobo.mnemovela import LocalMemoryService, MemoryObjectType

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    memory.upsert_subject(
        subject_id="subject/self",
        subject_type="person",
        display_name="Han",
        metadata={"role": "owner"},
    )
    memory.upsert_subject(
        subject_id="subject/alice",
        subject_type="person",
        display_name="Alice",
    )

    memory.upsert_entity(
        entity_id="entity/apple-tree",
        entity_type="plant",
        canonical_name="apple tree",
    )

    memory.upsert_object(
        object_id="object/private-self",
        object_type=MemoryObjectType.PERSON,
        display_name="Private self memory space",
    )
```

## Commit Typed Memories

The top-level package still exposes typed frames for the ten-type taxonomy. Applications should create frames from `axisrobo.mnemovela.types` exports and commit through the service or engine facade.

### Event memory

```python
from axisrobo.mnemovela import (
    EntityLink,
    Event5W2H,
    EventFrame,
    EventMeaning,
    EventProcess,
    LocalMemoryService,
    MemoryObjectLink,
    SubjectLink,
    SubjectScope,
)

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    commit = memory.commit_event(
        branch_name="main",
        event=EventFrame(
            event_5w2h=Event5W2H(
                who=("subject/self", "subject/alice"),
                what="Discussed planting an apple tree in the courtyard",
                when="2026-04-11T09:00:00Z",
                where="home/courtyard",
                why="to improve seasonal fruit supply",
                how="conversation",
            ),
            process=EventProcess(process_type="conversation"),
            meaning=EventMeaning(intentions=("plan garden work",), significance="shared planning"),
            subject_scope=SubjectScope.RELATIONAL,
            owner_subject_id="subject/self",
            participant_subject_ids=("subject/alice",),
            subject_links=(
                SubjectLink("subject/self", "owner", "relational", {}),
                SubjectLink("subject/alice", "participant", "relational", {}),
            ),
            entity_links=(EntityLink("entity/apple-tree", "object", 0.98, {}),),
            object_links=(MemoryObjectLink("object/private-self", "audience", "person", {}),),
            metadata={"source": "manual-example"},
        ),
    )
    print(commit.commit_id)
```

### Knowledge memory

```python
from axisrobo.mnemovela import KnowledgeAttributes, KnowledgeFrame, KnowledgeModality, LocalMemoryService, SubjectScope

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    commit = memory.commit_knowledge(
        branch_name="main",
        knowledge=KnowledgeFrame(
            concept="apple trees need winter pruning",
            ontology_type="cultivation_rule",
            claims=("Annual pruning improves shape and yield.",),
            attributes=KnowledgeAttributes(
                intrinsic={"species": "malus domestica"},
                state={"season": "winter"},
                source_refs=("guide/pruning-101",),
                confidence=0.85,
            ),
            modality=KnowledgeModality.ASSERTED,
            subject_scope=SubjectScope.PUBLIC,
            owner_subject_id="subject/self",
        ),
    )
    print(commit.commit_id)
```

### Experience, simulation, emotion, procedure, intention, belief, mission, and preference memory

The same pattern applies to `commit_experience(...)`, `create_simulation_branch(...)`, `commit_emotion(...)`, `commit_procedure(...)`, `commit_intention(...)`, `commit_belief(...)`, `commit_mission(...)`, and `commit_preference(...)`: construct the typed frame from top-level exports, then commit through the engine or service facade.

```python
from axisrobo.mnemovela import BeliefFrame, LocalMemoryService, MissionFrame, PreferenceFrame, SubjectScope

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    memory.commit_belief(
        branch_name="main",
        belief=BeliefFrame(
            subject_id="subject/self",
            schema_name="dispute_resolution_prior",
            belief_statements=("evidence-first conversations reduce escalation",),
            bias_tags=("risk-averse", "directness-preferred"),
            subject_scope=SubjectScope.SELF,
            owner_subject_id="subject/self",
        ),
    )

    memory.commit_mission(
        branch_name="main",
        mission=MissionFrame(
            mission_id="mission/dispute-042",
            title="Stabilize witness alignment before mediation",
            current_stage_index=2,
            current_state="in_progress",
            next_intention_id="intention/contact-witness",
            success_criteria=("witness confirms timeline",),
            blockers=("pending callback",),
            deadline="2026-04-12T07:30:00Z",
            subject_scope=SubjectScope.PROSPECTIVE,
            owner_subject_id="subject/self",
        ),
    )

    memory.commit_preference(
        branch_name="main",
        preference=PreferenceFrame(
            subject_id="subject/self",
            target_id="subject/xiaowang",
            cognitive_style={"risk_tolerance": -0.4, "reasoning_depth": 0.88},
            interaction_style={"tone": "direct", "cadence": "fast"},
            execution_style={"action_density": 0.78},
            subject_scope=SubjectScope.RELATIONAL,
            owner_subject_id="subject/self",
        ),
    )
```

## Ingest Media and Queue Deferred Extraction

Media ingestion is still a public API operation even though its real implementation now lives under `axisrobo.mnemovela.ingestion`.

```python
from axisrobo.mnemovela import LocalMemoryService, MediaExtractionMode, SubjectScope

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    source_commit = memory.ingest_media(
        branch_name="main",
        owner_subject_id="subject/self",
        subject_scope=SubjectScope.SELF,
        media_references=(
            {
                "uri": "file:///captures/orchard-walk.mp4",
                "mime_type": "video/mp4",
                "title": "Orchard Walk",
                "metadata": {
                    "transcript_text": "Alice inspects apple rows and discusses pruning.",
                    "detected_objects": ["apple tree", "ladder", "shears"],
                    "event_summary": "Alice inspects orchard rows and discusses pruning",
                },
            },
        ),
        extraction_modes=(
            MediaExtractionMode.TRANSCRIPT,
            MediaExtractionMode.OBJECT_DETECTION,
            MediaExtractionMode.EVENT_FRAME,
        ),
    )

    print(source_commit.commit_id)
    print(memory.list_media_references(source_commit.commit_id))
    print(memory.list_media_processing_jobs(source_commit_id=source_commit.commit_id))
```

## Structured Query and Hybrid Recall

Structured and ranked recall remain public engine/service APIs, while the planner and scoring internals now live under `axisrobo.mnemovela.querying`.

### Structured query

```python
from axisrobo.mnemovela import LocalMemoryService, MemoryObjectType, MemoryType, SubjectScope

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    commits = memory.query_memories(
        branch_name="main",
        subject_scope=SubjectScope.SELF,
        owner_subject_id="subject/self",
        entity_ids=("entity/apple-tree",),
        object_ids=("object/private-self",),
        object_types=(MemoryObjectType.PERSON,),
        memory_types=(MemoryType.EVENT, MemoryType.EXPERIENCE, MemoryType.INTENTION),
        limit=20,
    )

    for commit in commits:
        print(commit.memory_type, commit.commit_id, commit.payload)
```

The older `subject_entity_search(...)` name still works as a compatibility wrapper.

### Filter by retention tier

```python
from axisrobo.mnemovela import LocalMemoryService, RetentionState

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    cold_or_frozen = memory.query_memories(
        branch_name="main",
        retention_states=(RetentionState.COLD, RetentionState.FROZEN),
        limit=20,
    )

    hidden = memory.query_memories(
        branch_name="main",
        retention_states=(RetentionState.TOMBSTONED,),
        limit=20,
    )

    print([commit.retention_state for commit in cold_or_frozen])
    print([commit.commit_id for commit in hidden])
```

### Hybrid search with ranked results

```python
from axisrobo.mnemovela import LocalMemoryService, MemoryType, SubjectScope

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    results = memory.hybrid_search(
        "apple pruning",
        branch_name="main",
        subject_scope=SubjectScope.SELF,
        memory_types=(MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE),
        top_k=5,
        include_explanations=True,
    )

    for result in results:
        print(result.commit.commit_id, result.score, result.matched_modes)
        if result.explanation is not None:
            print(result.explanation.score_breakdown)
```

### Relation-only traversal

```python
from axisrobo.mnemovela import LocalMemoryService, RecallMode

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    results = memory.hybrid_search(
        branch_name="main",
        entity_ids=("entity/apple-tree",),
        modes=(RecallMode.RELATION,),
        top_k=10,
        include_explanations=True,
    )

    for result in results:
        print(result.commit.commit_id, result.matched_modes)
        if result.explanation is not None:
            print(result.explanation.relation_hits)
```

### Explain why a memory matched

```python
from axisrobo.mnemovela import LocalMemoryService, MemoryType

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    results = memory.hybrid_search(
        "apple pruning",
        branch_name="main",
        memory_types=(MemoryType.KNOWLEDGE,),
        top_k=1,
    )
    explanation = memory.explain_memory(
        results[0].commit.commit_id,
        query="apple pruning",
        branch_name="main",
        memory_types=(MemoryType.KNOWLEDGE,),
    )

    print(explanation.reasons)
    print(explanation.matched_filters)
    print(explanation.lineage)
```

## Snapshots and Maintenance

```python
from axisrobo.mnemovela import LocalMemoryService

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    memory.create_simulation_branch(branch_name="sim/trial-plan", from_branch="main", ttl_days=14)
    snapshot = memory.create_snapshot("main", label="before-simulation")
    state = memory.checkout_snapshot(snapshot.snapshot_id)

    print(snapshot.snapshot_id)
    print(len(state.commits))
```

```python
from axisrobo.mnemovela import LocalMemoryService

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    result = memory.run_maintenance("nightly", branch_name="main", max_jobs=10)
    print(result.scope)
    for task in result.tasks:
        print(task.scope, task.status, task.details)
```

Supported maintenance scopes in the current baseline are:

- `media`
- `retention`
- `retention-state`
- `consistency`
- `index-refresh`
- `simulation`
- `nightly`

## Backend and Index Extension Points

If you are implementing a custom backend or index, use the explicit contract layer rather than importing from internal implementation packages.

```python
from axisrobo.mnemovela.contracts import LexicalIndex, RelationIndex, SemanticIndex, StorageBackend
```

The compatibility module still works:

```python
from axisrobo.mnemovela.interfaces import StorageBackend
```

but new extension code should prefer `axisrobo.mnemovela.contracts`.

For legacy SQLite-specific compatibility imports, prefer the explicit compat layer instead of reaching into backend internals:

```python
from axisrobo.mnemovela.compat.sqlite import SQLiteBackend, SQLiteLexicalIndex, SQLiteRelationIndex, SQLiteSemanticIndex
```

Likewise, if you need stable exception types for integration boundaries, prefer:

```python
from axisrobo.mnemovela.core import BranchNotFoundError, MergeConflictError
```

The older compatibility path still works:

```python
from axisrobo.mnemovela.errors import BranchNotFoundError, MergeConflictError
```

## Run Deferred Media Extraction

```python
from axisrobo.mnemovela import LocalMemoryService

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    result = memory.run_maintenance("media", max_jobs=10)
    for task in result.tasks:
        print(task.scope, task.status, task.details)
```

## Check Consistency

Use `check_consistency(...)` to validate subject, entity, object, and ontology bindings over a branch or snapshot.

```python
from axisrobo.mnemovela import LocalMemoryService

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    report = memory.check_consistency(branch_name="main")
    print(report.issue_count)
    for issue in report.issues:
        print(issue.kind, issue.severity, issue.commit_id, issue.message)
```

## Review Knowledge Contradictions

Use the contradiction review queue when new knowledge conflicts with earlier claims or ontology assertions. `review_contradiction(...)` records workflow history in addition to changing status.

```python
from axisrobo.mnemovela import ContradictionReviewAction, ContradictionStatus, LocalMemoryService

with LocalMemoryService.from_sqlite("./agentic-memory.db") as memory:
    queue = memory.list_review_queue(branch_name="main")
    for item in queue:
        print(item.contradiction_kind, item.new_statement, item.existing_statement)

    open_commits = memory.query_memories(
        branch_name="main",
        contradiction_status=ContradictionStatus.OPEN,
    )
    print([commit.commit_id for commit in open_commits])

    if queue:
        memory.review_contradiction(
            queue[0].contradiction_id,
            action=ContradictionReviewAction.START_REVIEW,
            reviewer_id="reviewer-1",
            note="triage started",
        )
        memory.review_contradiction(
            queue[0].contradiction_id,
            action=ContradictionReviewAction.RESOLVE,
            reviewer_id="reviewer-2",
            note="evidence reconciled",
            resolution={"decision": "keep-both"},
        )

        for event in memory.list_contradiction_review_events(queue[0].contradiction_id):
            print(event.action, event.from_status, event.to_status, event.reviewer_id)
```

## Notes

- `LocalMemoryService` is a thin wrapper over `LocalMemoryEngine`, so the same methods are available on both.
- Typed commit helpers are the safest path because they preserve the semantic distinctions between memory classes.
- Use `query_memories(...)` for deterministic structured filtering.
- Use `hybrid_search(...)` when you need ranked results that combine structure, semantic similarity, and relation context.
- Use `RecallMode.LEXICAL` when exact keyword evidence should be a first-class recall signal.
- `subject_entity_search(...)` remains available for compatibility, but new integrations should prefer `query_memories(...)`.
- Relation traversal now expands through shared `subject`, `entity`, `object`, and `ontology` nodes rather than only parent or revert lineage.
- By default, `query_memories(...)` and `hybrid_search(...)` exclude `tombstoned` commits unless you opt in with `retention_states=(RetentionState.TOMBSTONED,)`.
- Use `create_simulation_branch(...)` when you want TTL-aware simulation branches instead of plain branches.
- Use `ingest_media(...)` to store media references as append-only source commits and queue deferred extraction work.
- Use `run_maintenance("media")` or `run_media_processing_job_once()` to materialize transcript, object-detection, and event-frame derivatives as new commits.
- Use `set_retention_state(...)` for explicit manual tier changes and `run_maintenance("retention-state")` for age-based reconciliation.
- Use `list_review_queue(...)`, `review_contradiction(...)`, and `list_contradiction_review_events(...)` to manage evidence-level knowledge conflicts without mutating existing commits.
- Use `run_maintenance(...)` instead of calling retention internals directly when you want operational orchestration.
- Use `check_consistency(...)` to surface missing catalog records, malformed ontology assertions, and stale bindings after revert or squash.