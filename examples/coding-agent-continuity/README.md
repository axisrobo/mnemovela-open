# Coding Agent Continuity — Engine-Level Pilot

Deterministic, self-contained pilot that exercises the full coding-agent
continuity flow using **only the Python engine's built-in capabilities**:
no MCP binary, no external LLM, no server process. All state lives in a local
SQLite file under a temporary directory.

## Run

From the repo root:

```powershell
py -3.13 examples/coding-agent-continuity/run_pilot.py
```

Exits `0` on success and prints a short summary. Any failed invariant assertion
exits non-zero with a message.

## What it demonstrates

Maps to product plan 18.1 steps 1-3:

| Step | Pilot action |
|---|---|
| 1. Capture (admission) | Session 1 uses `CaptureRouter(enable_admission=True)` to commit a project constraint, two decisions (rationale + alternatives), and a failed-build experience; a secret-laden event text is **rejected by admission** (no commit). |
| 2. Assembly | Session 2 calls `engine.build_context(query="continue Go verification task", budget=200)` on the same persistent SQLite store and asserts the constraint lands in the `constraints` partition, decisions in `current_work`, the failure in `experience`, the secret in **no** partition, and `budget_report.used <= 200`. |
| 3. Revision | `engine.revise(relation="supersede", ...)` supersedes decision #1; the rebuilt current view excludes the old decision while a `view="history"` search still serves it. |

## Expected output (abridged)

```
== Coding Agent Continuity pilot ==
tenant/project: acme/go-verification  principal: agent:dev
session 1 (CaptureRouter, admission ON):
  constraint  committed -> mem_...
  ...
  secret      REJECTED (admission_action=reject)
session 2 (build_context):
  current_work: 2 item(s), used=64
  experience: 1 item(s), used=22
  constraints: 1 item(s), used=10
  budget_report.used=96 (allocated=200)
  exclusions by category: none
  secret present in partitions: False
revision (supersede decision 1):
  old decision in current view: False
  old decision in history:      True
OK - pilot passed.
```

## Notes

- Uses local SQLite only (`tempfile.mkdtemp()` + `pilot.sqlite`); no external services.
- The regression test mirroring this flow lives at `tests/test_coding_agent_continuity.py`.
