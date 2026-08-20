# Mnemovela Agent Memory Skill

## When to use this skill

Load this skill when you want **persistent agent memory across coding sessions**.
Mnemovela stores decisions, facts, workspace state, project constraints, errors, and
task narratives as typed, searchable, branch-aware records. The agent retrieves
them at session start instead of re-discovering everything from file reads.

## Toolset

All interactions go through the Mnemovela MCP server. The 25 available tools are
grouped into five categories; this skill tells you when to use each.

### Recall (use BEFORE starting a task)

| Tool | When | Example |
|------|------|---------|
| `mneme.search_memory` | Search all memory for related past work, errors, concepts | `search_memory(query="{task/error/module}", top_k=5)` |
| `mneme.query_facts` | Find structured facts about an entity (decisions, constraints, tool ownership) | `query_facts(subject_id="module:go-protocol-mcp")` |
| `mneme.query_memories` | Filter by entity IDs and memory types (events, knowledge, procedures) | `query_memories(entity_ids=["constraint:no-env-credentials"], memory_types=["knowledge"])` |
| `mnemovela.build_context` | Get a compact context payload assembled from past episodes | `build_context(query="current project state", budget=800)` |
| `mneme.resolve_entity` | Check if a mention maps to a known entity | `resolve_entity(mention="dark mode", entity_type="concept")` |

### Write (use DURING or AFTER a task)

| Tool | When | Example |
|------|------|---------|
| `mneme.add_episode` | Record a task narrative (intent, changes, outcomes, pitfalls) | `add_episode(branch_name="main", content="{summary}", episode_type="development-summary")` |
| `mneme.add_fact` | Store a durable reusable truth about a module, file, or concept | `add_fact(fact_id="fact:{id}", subject_id="module:{name}", predicate="implements", object_value="{what}")` |
| `mneme.upsert_entity` | Register a new module, file, command, or concept entity | `upsert_entity(entity_id="module:theme-provider", entity_type="module", canonical_name="ThemeProvider.tsx")` |
| `mneme.upsert_subject` | Register a person or team as a subject | `upsert_subject(subject_id="team:frontend", subject_type="team", display_name="Frontend Team")` |
| `mneme.commit_memory` | Write a generic memory commit (any type + payload) | `commit_memory(branch_name="main", memory_type="knowledge", payload={...})` |

### Capture (use DURING a task, as events happen)

| Tool | When | Example |
|------|------|---------|
| `mneme.capture_decision` | Record a design choice with rationale and alternatives | `capture_decision(decision_summary="{what}", rationale="{why}", alternatives="{what else}")` |
| `mneme.capture_constraint` | Record a project invariant that future changes must preserve | `capture_constraint(constraint_summary="Theme colors must use CSS custom properties on :root")` |
| `mneme.capture_error` | Record a failure with diagnosis (even if fixed) | `capture_error(error_summary="{what failed}", tool_name="{if any}", context="{when}")` |
| `mneme.capture_tool_call` | Record a tool invocation (especially destructive or external ones) | `capture_tool_call(tool_name="gh pr create", input_json='{...}', output_summary="Created PR #42")` |

### Session (use at SESSION START and END)

| Tool | When | Example |
|------|------|---------|
| `mneme.session_start` | Initialize session with context retrieval | `session_start(query="current project state", tenant_id="default", project_id="default")` |
| `mneme.session_end` | End session, persist summary, changed files, decisions | `session_end(summary="{what was done}", changed_files='["a.ts","b.ts"]', decisions='["decision 1","decision 2"]')` |

### Maintenance (use periodically, not every session)

| Tool | When | Example |
|------|------|---------|
| `mneme.invalidate_fact` | Mark a fact as stale when source code or reality contradicts it | `invalidate_fact(fact_id="fact:old-ci-command", invalidated_at="{ISO-8601}", reason="CI now uses cargo nextest")` |
| `mneme.create_branch` | Create an experimental branch before risky work | `create_branch(branch_name="experiment/memory-index", from_branch="main")` |
| `mneme.merge_branch` | Merge an experimental branch back into main | `merge_branch(source_branch="experiment/memory-index", target_branch="main", strategy="manual")` |
| `mneme.list_branches` | List branches to find orphaned experiments | `list_branches()` |
| `mneme.extract_episode` | Run an offline extractor over a committed episode to derive entities/facts | `extract_episode(branch_name="main", episode_commit_id="mem_1", provider="offline")` |

---

## Start-of-task recall

Before reading any files, recall what Mnemovela already knows:

```
1. mneme.search_memory(query="{task description}", top_k=5, include_explanations=true)
   → Returns episodes, facts, decisions related to this task.
   → If results mention entity IDs, follow up with query_facts.

2. mnemovela.build_context(query="{task domain}", budget=800)
   → Returns assembled context from past episodes.

3. If the task touches a known module, query its facts:
   mneme.query_facts(subject_id="module:{name}")

4. If the task imposes a constraint, check for known constraints:
   mneme.query_memories(entity_ids=["constraint:{name}"], memory_types=["knowledge"])
```

Only use file-system search (grep/glob) for what memory does not cover or when
memory claims something that source contradicts (then invalidate the stale fact).

---

## During-work capture

**Decisions** (capture immediately after making a design choice):
```
mneme.capture_decision(
  decision_summary="<1-line summary>",
  rationale="<why this approach>",
  alternatives="<what else was considered>",
  branch_name="main"
)
```

**Errors** (capture after diagnosing, even if already fixed):
```
mneme.capture_error(
  error_summary="<what broke>",
  tool_name="<dep/call that failed>",
  context="<when it happened>",
  branch_name="main"
)
```

**Durable facts** (capture once, reuse across sessions):
- Module responsibilities: `module:<name> implements <capability>`
- File-to-feature map: `file:<path> implements <feature>`
- Command recipes: `command:<name> requires_env <VAR>`
- Test suite ownership: `module:<name> tested_by test-suite:<name>`

```
mneme.upsert_entity(entity_id="module:auth-middleware", entity_type="module", canonical_name="Auth middleware")
mneme.add_fact(fact_id="fact:auth-depends-on-session", subject_id="module:auth-middleware", predicate="depends_on", object_value="module:session-store")
```

---

## Workspace state

At the end of a session, persist what changed so the next session knows where
things stand:

```
mneme.session_end(
  summary="Added dark mode toggle. 5/5 tests pass.",
  changed_files='["src/theme/ThemeProvider.tsx", "src/styles/theme.css", "src/pages/Settings.tsx"]',
  decisions='["Use CSS custom properties on :root for theme variables"]',
  session_id="{current}",
  branch_name="main"
)
```

For long-running work, periodically commit workspace state as a **workspace**
frame:

```
mneme.commit_memory(
  branch_name="main",
  memory_type="workspace_state",
  payload={
    "active_files": ["ThemeProvider.tsx", "theme.css"],
    "pending_decisions": ["animation strategy for dark-mode toggle"],
    "known_gaps": ["Flash-of-light on initial load"],
    "test_status": {"unit": "5/5", "integration": "untested"}
  }
)
```

---

## Project-level knowledge management

### Entity ID convention

Use stable, typed entity IDs so facts form a searchable graph:

| Prefix | Pattern | Example |
|--------|---------|---------|
| `module:` | Logical module/component | `module:auth-middleware` |
| `file:` | Source file path (repo-relative) | `file:src/theme/ThemeProvider.tsx` |
| `command:` | Build/test/deploy command | `command:go-test-all` |
| `service:` | Deployed service/endpoint | `service:user-api` |
| `protocol:` | Communication protocol | `protocol:mcp` |
| `concept:` | Abstract concept / domain term | `concept:dark-mode` |
| `constraint:` | Project invariant | `constraint:no-creds-in-env` |
| `test-suite:` | Test suite name | `test-suite:theme-unit` |
| `decision:` | Archived design decision | `decision:css-vars-for-theming` |
| `error:` | Known failure signature | `error:flash-of-light-dark-mode` |

### Fact predicate vocabulary

Use consistent predicates so queries work across sessions:

| Predicate | Meaning | Example object |
|-----------|---------|----------------|
| `implements` | File/module implements a feature or concept | `module:theme-provider implements concept:dark-mode` |
| `depends_on` | Module/service depends on another entity | `module:auth depends_on module:session-store` |
| `tested_by` | Module is covered by a test suite | `module:theme-provider tested_by test-suite:theme-unit` |
| `requires_env` | Command requires an environment variable | `command:go-test-all requires_env CGO_ENABLED=0` |
| `known_failure` | Error signature maps to a known cause/fix | `error:flash-of-light known_failure "Missing initial style tag — inject a blocking <style> in <head>"` |
| `decision` | Archived design decision with rationale | `decision:css-vars-for-theming decision "Use CSS custom properties on :root because least churn"` |
| `constraint` | Invariant to preserve | `constraint:no-creds-in-env constraint "Never commit .env files or hardcode API keys"` |
| `owner` | Subject (team/person) owns a module/service | `module:theme-provider owner team:frontend` |

---

## Memory retrieval patterns

### Find everything about a module
```
mneme.query_facts(subject_id="module:{name}")
mneme.query_memories(entity_ids=["module:{name}"], memory_types=["event","knowledge","episode"])
mneme.search_memory(query="module:{name}", top_k=10)
```

### Check for constraints before a change
```
mneme.query_facts(predicate="constraint")
mneme.query_memories(entity_ids=["constraint:{domain}"], memory_types=["knowledge"])
```

### Find past errors matching a symptom
```
mneme.search_memory(query="{error symptom}", top_k=5)
→ If a matching error entity appears, query_memories for its known_failure facts.
```

### Reconstruct project state
```
mnemovela.build_context(query="current project state completed tasks open issues", budget=1200)
```

---

## Background maintenance

Run periodically (not every session — e.g., weekly or after a milestone):

### Invalidate stale facts

When source code contradicts a stored fact, invalidate it with a reason:
```
mneme.invalidate_fact(
  fact_id="fact:old-ci-command",
  invalidated_at="2026-07-08T12:00:00Z",
  reason="CI migrated from npm run test to cargo nextest"
)
```

### List orphaned experimentation branches
```
mneme.list_branches()
→ If an experiment branch hasn't been touched in weeks, merge or archive it.
```

### Extract entities/facts from raw episodes

Episodes that were committed as raw narrative can be processed through the
offline extractor to derive structured entities and facts automatically:
```
mneme.extract_episode(branch_name="main", episode_commit_id="mem_{id}", provider="offline")
```
This populates the knowledge graph from narrative content without manual
fact entry.

### Clean up retention

On the server side (not from the agent — via the JSON-RPC or REST surface):
- `mneme.reconcile_retention` — promotes/demotes memory by hot/warm/cold/frozen tiers
- `mneme.reconcile_forgetting` — tombstones or purges memory past policy thresholds

These are **admin operations**, not agent operations. Run them from a cron job
or maintenance script against the running server.

---

## What NOT to store

- **Credentials, tokens, `.env` values, API keys** — never persist to memory.
- **Raw full transcripts** — store compressed summaries with source IDs, not the
  full tool output.
- **Guesses** — only store verified knowledge. If uncertain, don't write.
- **Facts derivable from file names** — e.g., don't store "file:main.go exists".
- **Private scripts or paths** — sanitize anything that leaks internal structure.

---

## Integration summary

- [Mnemovela Cognitive Memory Taxonomy](reference/memory-taxonomy.md) — full 14-type reference with schema-accurate `commit_memory` examples per type

| Agent | Config location | Skill location |
|-------|----------------|----------------|
| **OpenCode** | `opencode.json` (project root) — add the Mnemovela MCP server entry | `.opencode/skills/mnemovela-agent-memory/SKILL.md` (this file) |
| **Claude Code** | `~/.claude/settings.json` — add the Mnemovela MCP server entry | Project-level `CLAUDE.md` or agent instruction |
| **Codex** | `~/.codex/config.toml` — add the Mnemovela MCP server entry | Project-level `AGENTS.md` or hooks |
