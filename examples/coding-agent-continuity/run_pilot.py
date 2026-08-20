"""Coding Agent Continuity — deterministic engine-level pilot.

Runs the full capture -> admission -> assembly -> revise flow with only the
Python engine's built-in capabilities (no MCP binary, no external LLM):

  Product plan 18.1:
    1. Session 1: CaptureRouter (admission ON) captures a project constraint,
       two decisions (chosen_option / rationale / alternatives), and a failed
       build experience. A secret-laden event text is submitted and MUST be
       rejected by admission (no commit).
    2. Session 2: build_context over the same persistent SQLite store restores
       the constraint into the ``constraints`` partition, the decisions into
       ``current_work``, and the failure into ``experience``; the secret never
       appears in any partition; the budget invariant holds.
    3. Revision: supersede decision #1, rebuild the current view, and verify the
       old decision is consumed out of the current view while history still
       serves it.

Path chosen (documented per plan step): all captures go through
``CaptureRouter.route`` so the pilot exercises the real capture path.
``CaptureRouter`` maps each tool to a typed memory commit
(``capture_constraint`` -> ``constraint``, ``capture_decision`` -> ``decision``,
``capture_error`` -> ``experience``, ``capture_session_end`` -> ``event``) and
flattens the structured decision payload (chosen_option / rationale /
alternatives) into the summary text it commits. Commits land via
``LocalMemoryEngine.commit`` with ``payload={"summary": ...}``.

Admission rejection is verified against the raw secret text: the admission
engine's secret scan flags ``sk-...`` and ``password=letmein`` as blockers, so
the router returns ``{"commit_id": None, "admission_action": "reject"}`` and no
row is written.

Run from the repo root:

    py -3.13 examples/coding-agent-continuity/run_pilot.py

Exits 0 on success; any failed assertion exits non-zero with a message.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python" / "src"))

from axisrobo.mnemovela.backends import SQLiteBackend
from axisrobo.mnemovela.backends.sqlite import SQLiteLexicalIndex, SQLiteRelationIndex, SQLiteSemanticIndex
from axisrobo.mnemovela.capture_router import CaptureRouter
from axisrobo.mnemovela.contracts.storage import AccessContext
from axisrobo.mnemovela.engine import LocalMemoryEngine

TENANT = "acme"
PROJECT = "go-verification"
PRINCIPAL = ("agent:dev",)

CGO_CONSTRAINT = "Use CGO_ENABLED=0 for local Go verification on Windows."
DECISION_1_SUMMARY = "Run the Go suite with CGO_ENABLED=0 before every merge."
DECISION_2_SUMMARY = "Keep the Python core the single source of truth for Go parity."
EXPERIENCE_TEXT = "Local go build failed with 'cgo: C compiler \"gcc\" not found' on Windows."
SECRET_TEXT = "The API key is sk-abcdefghijklmnopqrstuvwxyz1234567890 and password=letmein"

BUDGET = 200
QUERY = "continue Go verification task"


def _build_context(engine: LocalMemoryEngine, *, access_context: AccessContext) -> dict:
    return engine.build_context(
        query=QUERY,
        branch_name="main",
        budget=BUDGET,
        access_context=access_context,
    )


def _partition_items(bundle: dict, partition: str) -> list[dict]:
    for entry in bundle.get("partitions", []):
        if entry.get("partition") == partition:
            return list(entry.get("items", []))
    return []


def _all_item_texts(bundle: dict) -> list[str]:
    return [item["text"] for entry in bundle.get("partitions", []) for item in entry.get("items", [])]


def run_pilot(engine: LocalMemoryEngine, *, access_context: AccessContext) -> int:
    # --- Session 1: capture with admission ON ---------------------------------
    router = CaptureRouter(engine, enable_admission=True)

    constraint_out = router.route(
        "capture_constraint",
        {"constraint_summary": CGO_CONSTRAINT, "scope": "project"},
        branch_name="main",
    )
    decision_1_out = router.route(
        "capture_decision",
        {
            "decision_summary": DECISION_1_SUMMARY,
            "rationale": "The Go backends (Pebble and in-memory) must compile without a C toolchain.",
            "alternatives": ["Install MSYS2 gcc", "Skip local Go verification"],
        },
        branch_name="main",
    )
    decision_2_out = router.route(
        "capture_decision",
        {
            "decision_summary": DECISION_2_SUMMARY,
            "rationale": "Go parity tests must match Python fixtures; divergence is a bug.",
            "alternatives": ["Port tests to Go only", "Drop Go parity checks"],
        },
        branch_name="main",
    )
    experience_out = router.route(
        "capture_error",
        {"error_summary": EXPERIENCE_TEXT, "tool_name": "go build", "context": "first local verification attempt"},
        branch_name="main",
    )
    secret_out = router.route(
        "capture_session_end",
        {"session_id": "session-1", "summary": SECRET_TEXT, "changed_files": [], "decisions": []},
        branch_name="main",
    )

    # Invariances for session 1.
    assert constraint_out["commit_id"] is not None, "constraint must be committed"
    assert decision_1_out["commit_id"] is not None, "decision 1 must be committed"
    assert decision_2_out["commit_id"] is not None, "decision 2 must be committed"
    assert experience_out["commit_id"] is not None, "experience must be committed"
    assert secret_out["admission_action"] == "reject", f"secret must be rejected, got {secret_out}"
    assert secret_out["commit_id"] is None, "rejected secret must not commit"
    assert engine.get_commit(secret_out["commit_id"] if secret_out["commit_id"] else "") is None

    # --- Session 2: build_context restores the persistent memory --------------
    bundle = _build_context(engine, access_context=access_context)

    constraints = _partition_items(bundle, "constraints")
    current_work = _partition_items(bundle, "current_work")
    experience_items = _partition_items(bundle, "experience")
    all_texts = _all_item_texts(bundle)

    assert any(CGO_CONSTRAINT in item["text"] for item in constraints), "CGO constraint must be in constraints partition"
    assert any(DECISION_1_SUMMARY in item["text"] for item in current_work), "decision 1 must be in current_work"
    assert any(DECISION_2_SUMMARY in item["text"] for item in current_work), "decision 2 must be in current_work"
    assert any(EXPERIENCE_TEXT in item["text"] for item in experience_items), "failure experience must be in experience partition"
    assert not any("sk-abcdefghijklmnopqrstuvwxyz1234567890" in text or "letmein" in text for text in all_texts), "secret must not appear in any partition"
    assert bundle["budget_report"]["used"] <= BUDGET, "budget invariant violated"

    # --- Revision: supersede decision #1 ---------------------------------------
    revised = engine.revise(
        branch_name="main",
        relation="supersede",
        predecessor_ids=[decision_1_out["commit_id"]],
        reason="The verification loop now requires both go vet and go test.",
        memory_type="decision",
        payload={"summary": "Run go vet and go test with CGO_ENABLED=0 before every merge."},
        access_context=access_context,
    )
    assert revised.commit_id is not None

    current_bundle = _build_context(engine, access_context=access_context)
    current_texts = _all_item_texts(current_bundle)
    assert DECISION_1_SUMMARY not in " ".join(current_texts), "superseded decision must not appear in the current view"

    history = engine.hybrid_search(
        QUERY,
        branch_name="main",
        view="history",
        top_k=50,
        access_context=access_context,
    )
    history_texts = []
    for result in history:
        payload = dict(result.commit.payload or {})
        history_texts.append(str(payload.get("summary") or payload.get("content") or ""))
    assert any(DECISION_1_SUMMARY in text for text in history_texts), "superseded decision must still be in history"

    # --- Compact summary -------------------------------------------------------
    print("== Coding Agent Continuity pilot ==")
    print(f"tenant/project: {TENANT}/{PROJECT}  principal: {PRINCIPAL[0]}")
    print("session 1 (CaptureRouter, admission ON):")
    print(f"  constraint  committed -> {constraint_out['commit_id']}")
    print(f"  decision 1  committed -> {decision_1_out['commit_id']}")
    print(f"  decision 2  committed -> {decision_2_out['commit_id']}")
    print(f"  experience  committed -> {experience_out['commit_id']}")
    print(f"  secret      REJECTED (admission_action={secret_out['admission_action']})")
    print("session 2 (build_context):")
    for entry in bundle.get("partitions", []):
        print(f"  {entry['partition']}: {len(entry['items'])} item(s), used={entry['used']}")
    by_category: dict[str, int] = {}
    for exclusion in bundle.get("exclusions", []):
        category = exclusion.get("category", "unknown")
        by_category[category] = by_category.get(category, 0) + 1
    print(f"  budget_report.used={bundle['budget_report']['used']} (allocated={BUDGET})")
    print(f"  exclusions by category: {by_category or 'none'}")
    print(f"  secret present in partitions: {any('sk-abcdef' in t or 'letmein' in t for t in all_texts)}")
    print("revision (supersede decision 1):")
    print(f"  old decision in current view: {DECISION_1_SUMMARY in ' '.join(current_texts)}")
    print(f"  old decision in history:      {any(DECISION_1_SUMMARY in t for t in history_texts)}")
    print("OK - pilot passed.")
    return 0


def main() -> int:
    temp_dir = tempfile.mkdtemp(prefix="mnemovela-pilot-")
    db_path = Path(temp_dir) / "pilot.sqlite"
    access_context = AccessContext(
        tenant_id=TENANT,
        project_id=PROJECT,
        principal_subject_ids=PRINCIPAL,
    )
    engine = LocalMemoryEngine(
        SQLiteBackend(db_path),
        lexical_index=SQLiteLexicalIndex(db_path),
        relation_index=SQLiteRelationIndex(db_path),
        semantic_index=SQLiteSemanticIndex(db_path),
        access_context=access_context,
    )
    try:
        return run_pilot(engine, access_context=access_context)
    finally:
        engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
