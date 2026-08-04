# Mnemovela Cognitive Memory Taxonomy

Mnemovela has **14 distinct memory types**, each with its own schema, retention
profile, and retrieval semantics. This guide covers when to use each type and
shows concrete `commit_memory` examples for agent use.

Refer back to the [companion skill](../SKILL.md) for the full
workflow — this document is the type reference.

## Choosing a type

| If you want to store... | Use this type | Why |
|-------------------------|---------------|-----|
| A raw observation or log entry | **event** | 5W2H + evidence + role bindings — the richest descriptive frame |
| A stable truth about the world | **knowledge** | Structured claims with confidence, temporal context, and causal dynamics |
| A reflection after an action | **experience** | Outcome + salience + interpretation — "what went well / poorly" |
| A hypothetical scenario | **simulation** | Initial state + operators + possible outcomes — "what if" reasoning |
| An emotional state or response | **emotion** | Valence/arousal scores linked to a triggering event |
| A step-by-step recipe | **procedure** | Preconditions + action steps — reusable how-to knowledge |
| A goal to achieve | **intention** | Target state + motivation + deadline — tracks agent plans |
| A worldview assumption | **belief** | Schemas with prior/current state + confidence — tracks belief revision |
| A mission tracking progress | **mission** | Multi-stage task with stage events — tracks long-running undertakings |
| A style or UX preference | **preference** | Cognitive/interaction/sensory/execution dimensions |
| A snapshot of the current task | **workspace_state** | Active files, pending decisions, test status — transient task-local state |
| An archived design decision | **decision** | Decision + rationale + alternatives — audit trail |
| A project invariant | **constraint** | A rule future work must respect |
| How two entities relate | **relationship** | Subject/object with binding type — knowledge graph edges |

---

## Type reference

### event

The canonical descriptive memory. Use for raw observations, tool outputs,
user messages, and system events.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="event",
  payload={
    "summary": "User reported that dark mode toggle flashes white on first load",
    "event_5w2h": {
      "who": ["user:alice"],
      "what": "dark mode flash-of-white bug",
      "when": "2026-07-08T14:00:00Z",
      "where": "production (Chrome 126, macOS)",
      "why": "CSS custom properties not applied before first paint",
      "how": "reproducible by clearing cache and reloading"
    },
    "evidence": [
      {"source_type": "screenshot", "source_ref": "https://...", "reliability": 1.0},
      {"source_type": "user-report", "source_ref": "issue #142", "reliability": 0.9}
    ],
    "role_bindings": [
      {"entity_id": "module:theme-provider", "role": "subject"},
      {"entity_id": "concept:dark-mode", "role": "affected"}
    ]
  }
)
```

### knowledge

Stable, declarative truths. Has the richest structure: concept, ontology type,
claims, attributes (intrinsic/state/source), axioms, temporal context, and
causal dynamics.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="knowledge",
  payload={
    "concept": "CSS custom properties for theming",
    "claims": [
      "CSS custom properties defined on :root are inherited by all elements",
      "A blocking <style> tag in <head> prevents the flash-of-unstyled-content"
    ],
    "attributes": {
      "intrinsic": {"scope": "global", "cascade": "inherited"},
      "state": {"applied": true, "fallback": "none"},
      "confidence": 0.95,
      "source_refs": ["spec:css-variables", "mdn:custom-properties"]
    },
    "context": {
      "domain": "browser-rendering",
      "valid_from": "2026-07-08T00:00:00Z"
    },
    "dynamics": {
      "causes": ["<link rel=stylesheet> loads after first paint if not in <head>"],
      "effects": ["white flash on dark mode pages"],
      "preconditions": ["dark mode enabled", "CSS-in-JS runtime injects styles lazily"]
    }
  }
)
```

### experience

Reflection after an action. Captures what was observed, what mattered, and
what the outcome was.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="experience",
  payload={
    "event_commit_id": "mem_3",
    "observations": [
      "Injecting a <style> tag in <head> via document.createElement eliminated the flash",
      "CSS-in-JS runtime conflates style injection with component mounting"
    ],
    "interpretation": "The root cause is not CSS variables but late style injection timing",
    "outcome": "Fixed by adding a blocking <style> tag before any component renders",
    "salience_map": {"root_cause_quality": 0.9, "fix_simplicity": 0.8, "risk_of_recurrence": 0.2}
  }
)
```

### simulation

Hypothetical reasoning. Model initial state, apply operators, and rank outcomes.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="simulation",
  payload={
    "subject_id": "agent:opencode",
    "initial_state": {"dark_mode": "enabled", "style_injection": "runtime", "flash_present": true},
    "operators": [
      "switch to build-time CSS extraction",
      "inject blocking <style> in <head>",
      "use server-side rendering for initial styles"
    ],
    "possible_outcomes": [
      {"description": "Build-time extraction — no flash but adds build step", "probability": 0.9, "utility": 0.7},
      {"description": "Blocking <style> — no flash, minimal change", "probability": 0.95, "utility": 0.85},
      {"description": "SSR styles — no flash, requires SSR infra", "probability": 0.8, "utility": 0.6}
    ],
    "selected_outcome": "Blocking <style> — no flash, minimal change"
  }
)
```

### emotion

Affective state. Links to the triggering event, carries valence/arousal, and
threat/reward/attachment scores.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="emotion",
  payload={
    "linked_event_commit_id": "mem_42",
    "emotion_vector": {"valence": -0.4, "arousal": 0.6},
    "threat_score": 0.1,
    "reward_score": 0.3,
    "source_commit_ids": ["mem_42"]
  }
)
```

### procedure

A reusable step-by-step process. Stores preconditions, ordered action steps
with expected outcomes, and links to related knowledge.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="procedure",
  payload={
    "name": "diagnose-css-flash-of-unstyled-content",
    "trigger_pattern": "dark mode / theme shows wrong colors briefly on first load",
    "preconditions": ["dark mode enabled", "styles loaded async"],
    "action_steps": [
      {"step_id": "1", "description": "Open DevTools Performance tab and record a page load", "expected_outcome": "Timeline shows style injection relative to first paint"},
      {"step_id": "2", "description": "Check if a blocking <style> tag exists in <head>", "expected_outcome": "Presence/absence of inline styles before any <link> or <script>"},
      {"step_id": "3", "description": "If missing, add a <style> with :root custom properties as the first child of <head>", "expected_outcome": "No flash on subsequent loads"}
    ],
    "linked_knowledge_ids": ["knowledge:css-vars-inherit", "knowledge:blocking-style-tag"]
  }
)
```

### intention

An agent goal. Carries target state, motivation level, priority, deadline, and
success criteria.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="intention",
  payload={
    "subject_id": "agent:opencode",
    "target_state": {"dark_mode": "enabled", "flash_free": true, "tested": "all platforms"},
    "motivation_level": 0.9,
    "priority": 0.8,
    "deadline": "2026-07-09T18:00:00Z",
    "success_criteria": [
      "No white flash on Chrome/Firefox/Safari",
      "System preference detection works",
      "5/5 unit tests pass",
      "Zero visual-regression diffs"
    ]
  }
)
```

### belief

A worldview assumption that may be revised. Tracks schema, belief statements,
prior state, and confidence.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="belief",
  payload={
    "subject_id": "agent:opencode",
    "schema_name": "css-loading-behavior",
    "belief_statements": ["CSS custom properties defined on :root are always available before first paint"],
    "prior_state": {"confidence": 0.9, "evidence": ["MDN docs", "spec reading"]},
    "confidence": 0.3,
    "prior_strength": 0.8
  }
)
```

### mission

A long-running, multi-stage undertaking. Tracks stage progress and linked events.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="mission",
  payload={
    "mission_id": "dark-mode-rollout",
    "title": "Dark mode support across all surfaces",
    "current_stage_index": 1,
    "current_stage_label": "Fix rendering glitches",
    "current_state": "in_progress",
    "stage_event_commit_ids": ["mem_10", "mem_42"]
  }
)
```

### preference

Style, UX, and execution preferences. Captures how an agent or user likes
things done.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="preference",
  payload={
    "subject_id": "agent:opencode",
    "cognitive_style": {"prefers_explicit": true, "wants_alternatives": true},
    "execution_style": {"test_first": true, "commit_frequency": "per-task"},
    "interaction_style": {"verbose_errors": false}
  }
)
```

### workspace_state

Transient task-local state. Captures active files, pending decisions, test
status — overwritten each session, not accumulated.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="workspace_state",
  payload={
    "active_files": ["src/theme/ThemeProvider.tsx", "src/styles/theme.css"],
    "pending_decisions": ["animation strategy for dark-mode toggle"],
    "known_gaps": ["Flash-of-light on initial load"],
    "test_status": {"unit": "5/5", "integration": "0/0"},
    "last_activity": "committed fix for flash-of-white on dark mode load"
  }
)
```

### decision

An archived design decision. Stores the choice, rationale, and alternatives
considered.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="decision",
  payload={
    "decision": "Use CSS custom properties on :root for theme variables",
    "rationale": "Least churn on existing components; works with both CSS-in-JS and plain CSS",
    "alternatives": "Tailwind dark: prefix (doubles class names), separate stylesheets (maintenance burden)",
    "context": "Dark mode rollout — needed a theming strategy that works across 40+ components",
    "outcome": "Implemented; flash-of-white bug was unrelated (late style injection, not CSS vars)"
  }
)
```

### constraint

A project invariant that future work must respect.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="constraint",
  payload={
    "constraint": "All theme colors must be defined as CSS custom properties on :root, never hardcoded in components",
    "scope": "all frontend code",
    "enforcement": "ESLint rule `no-hardcoded-colors`; CI gate on PRs"
  }
)
```

### relationship

How two entities relate. Use for knowledge-graph edges between subjects,
objects, concepts, and modules.

```
mnemovela.commit_memory(
  branch_name="main",
  memory_type="relationship",
  payload={
    "subject_id": "module:theme-provider",
    "object_id": "constraint:no-hardcoded-colors",
    "relation_type": "implements",
    "metadata": {"scope": "enforcement"}
  }
)
```

---

## When to use add_fact vs commit_memory

| Use `add_fact` when... | Use `commit_memory` when... |
|------------------------|----------------------------|
| You have a single subject-predicate-object triple | You have rich structured content with many fields |
| The fact is independent and reusable | The content fits a specific cognitive frame |
| You want simple query-by-subject | You want typed retrieval and schema validation |
| Example: `module:X implements concept:Y` | Example: a full knowledge frame with claims, context, causality |
