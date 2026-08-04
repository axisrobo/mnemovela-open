from __future__ import annotations

from typing import Any

import grpc

from mnemovela_client._generated import mnemovela_v1_pb2 as pb
from mnemovela_client._generated import mnemovela_v1_pb2_grpc as pb_grpc
from mnemovela_client._json import to_value_map, from_value_map
from mnemovela_client.errors import MnemeError


def _commit_to_dict(c: "pb.Commit") -> dict[str, Any]:
    return {
        "sequence": c.sequence,
        "commit_id": c.commit_id,
        "branch_name": c.branch_name,
        "memory_type": c.memory_type,
        "retention_state": c.retention_state,
        "created_at": c.created_at,
        "tenant_id": c.tenant_id,
        "project_id": c.project_id,
        "owner_subject_id": c.owner_subject_id,
        "parent_commit_ids": list(c.parent_commit_ids),
        "payload": from_value_map(c.payload),
        "metadata": from_value_map(c.metadata),
    }


def _fact_to_dict(f) -> dict[str, Any]:
    return {
        "fact_id": f.fact_id,
        "subject_id": f.subject_id,
        "predicate": f.predicate,
        "object_value": f.object_value,
        "confidence": f.confidence,
        "valid_from": f.valid_from,
        "valid_to": f.valid_to,
        "source_commit_id": f.source_commit_id,
        "branch_name": f.branch_name,
    }


def _run_to_dict(r) -> dict[str, Any]:
    return {
        "run_id": r.run_id,
        "episode_commit_id": r.episode_commit_id,
        "branch_name": r.branch_name,
        "provider_id": r.provider_id,
        "fingerprint": r.fingerprint,
        "status": r.status,
        "derived_commit_ids": list(r.derived_commit_ids),
        "error": r.error,
    }


class MnemeClient:
    def __init__(self, address: str = "localhost:9090"):
        self._channel = grpc.insecure_channel(address)
        self._stub = pb_grpc.MnemeStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def __enter__(self) -> "MnemeClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _call(self, method, request):
        try:
            return method(request)
        except grpc.RpcError as err:
            raise MnemeError.from_rpc_error(err) from err

    # ── typed writes ────────────────────────────────────────────────
    def add_episode(self, *, branch_name: str, content: str, episode_type: str = "",
                    source: str = "", observed_at: str = "", tenant_id: str = "",
                    project_id: str = "") -> dict[str, Any]:
        req = pb.AddEpisodeRequest(branch_name=branch_name, content=content,
                                   episode_type=episode_type, source=source,
                                   observed_at=observed_at, tenant_id=tenant_id,
                                   project_id=project_id)
        return _commit_to_dict(self._call(self._stub.AddEpisode, req).commit)

    def commit_memory(self, *, branch_name: str, memory_type: str,
                      payload: dict[str, Any] | None = None,
                      metadata: dict[str, Any] | None = None,
                      owner_subject_id: str = "", tenant_id: str = "",
                      project_id: str = "") -> dict[str, Any]:
        req = pb.CommitMemoryRequest(branch_name=branch_name, memory_type=memory_type,
                                     owner_subject_id=owner_subject_id, tenant_id=tenant_id,
                                     project_id=project_id)
        for k, v in to_value_map(payload or {}).items():
            req.payload[k].CopyFrom(v)
        for k, v in to_value_map(metadata or {}).items():
            req.metadata[k].CopyFrom(v)
        return _commit_to_dict(self._call(self._stub.CommitMemory, req).commit)

    def add_fact(self, *, branch_name: str, fact_id: str, subject_id: str, predicate: str,
                 object_value: str, valid_from: str = "", valid_to: str = "",
                 confidence: float = 0.0, tenant_id: str = "",
                 project_id: str = "") -> dict[str, Any]:
        req = pb.AddFactRequest(branch_name=branch_name, fact_id=fact_id, subject_id=subject_id,
                                predicate=predicate, object_value=object_value,
                                valid_from=valid_from, valid_to=valid_to, confidence=confidence,
                                tenant_id=tenant_id, project_id=project_id)
        return _commit_to_dict(self._call(self._stub.AddFact, req).commit)

    def invalidate_fact(self, *, branch_name: str, fact_id: str, invalidated_at: str,
                        reason: str = "", tenant_id: str = "",
                        project_id: str = "") -> dict[str, Any]:
        req = pb.InvalidateFactRequest(branch_name=branch_name, fact_id=fact_id,
                                       invalidated_at=invalidated_at, reason=reason,
                                       tenant_id=tenant_id, project_id=project_id)
        return _commit_to_dict(self._call(self._stub.InvalidateFact, req).commit)

    def upsert_subject(self, *, subject_id: str, subject_type: str, display_name: str = "",
                       tenant_id: str = "", project_id: str = "") -> dict[str, Any]:
        req = pb.UpsertSubjectRequest(subject_id=subject_id, subject_type=subject_type,
                                      display_name=display_name, tenant_id=tenant_id,
                                      project_id=project_id)
        resp = self._call(self._stub.UpsertSubject, req)
        return {"subject_id": resp.subject_id}

    def upsert_entity(self, *, entity_id: str, entity_type: str, canonical_name: str = "",
                      metadata: dict[str, Any] | None = None, tenant_id: str = "",
                      project_id: str = "") -> dict[str, Any]:
        req = pb.UpsertEntityRequest(entity_id=entity_id, entity_type=entity_type,
                                     canonical_name=canonical_name, tenant_id=tenant_id,
                                     project_id=project_id)
        for k, v in to_value_map(metadata or {}).items():
            req.metadata[k].CopyFrom(v)
        resp = self._call(self._stub.UpsertEntity, req)
        return {"entity_id": resp.entity_id}

    # ── queries ─────────────────────────────────────────────────────
    def search_memory(self, branch_name: str, query: str, *, top_k: int = 20,
                      entity_ids: list[str] | None = None) -> list[dict[str, Any]]:
        req = pb.SearchMemoryRequest(branch_name=branch_name, query=query, top_k=top_k,
                                     entity_ids=entity_ids or [])
        resp = self._call(self._stub.SearchMemory, req)
        return [{"commit": _commit_to_dict(r.commit), "score": r.score,
                 "matched_modes": list(r.matched_modes)} for r in resp.results]

    def query_memories(self, *, branch_name: str, entity_ids: list[str] | None = None,
                       limit: int = 50, tenant_id: str = "",
                       project_id: str = "") -> list[dict[str, Any]]:
        req = pb.QueryMemoriesRequest(branch_name=branch_name, entity_ids=entity_ids or [],
                                      limit=limit, tenant_id=tenant_id, project_id=project_id)
        resp = self._call(self._stub.QueryMemories, req)
        return [_commit_to_dict(c) for c in resp.commits]

    def query_facts(self, *, branch_name: str = "", fact_id: str = "", subject_id: str = "",
                    predicate: str = "", true_at: str = "", include_invalidated: bool = False,
                    limit: int = 50, tenant_id: str = "",
                    project_id: str = "") -> list[dict[str, Any]]:
        req = pb.QueryFactsRequest(branch_name=branch_name, fact_id=fact_id, subject_id=subject_id,
                                   predicate=predicate, true_at=true_at,
                                   include_invalidated=include_invalidated, limit=limit,
                                   tenant_id=tenant_id, project_id=project_id)
        resp = self._call(self._stub.QueryFacts, req)
        return [_fact_to_dict(f) for f in resp.facts]

    # ── resolution ──────────────────────────────────────────────────
    def resolve_entity(self, *, mention: str, entity_type: str = "", tenant_id: str = "",
                       project_id: str = "") -> dict[str, Any]:
        req = pb.ResolveEntityRequest(mention=mention, entity_type=entity_type,
                                      tenant_id=tenant_id, project_id=project_id)
        resp = self._call(self._stub.ResolveEntity, req)
        return {"entity_id": resp.entity_id, "entity_type": resp.entity_type,
                "canonical_name": resp.canonical_name}

    def resolve_entity_explained(self, *, mention: str, entity_type: str = "", tenant_id: str = "",
                                 project_id: str = "") -> dict[str, Any]:
        req = pb.ResolveEntityExplainedRequest(mention=mention, entity_type=entity_type,
                                               tenant_id=tenant_id, project_id=project_id)
        resp = self._call(self._stub.ResolveEntityExplained, req)
        return {"matched": resp.matched, "match_type": resp.match_type,
                "matched_value": resp.matched_value, "confidence": resp.confidence,
                "entity": {"entity_id": resp.entity.entity_id,
                           "entity_type": resp.entity.entity_type,
                           "canonical_name": resp.entity.canonical_name}}

    # ── extraction ──────────────────────────────────────────────────
    def extract_episode(self, *, branch_name: str, episode_commit_id: str, provider: str = "",
                        tenant_id: str = "", project_id: str = "") -> dict[str, Any]:
        req = pb.ExtractEpisodeRequest(branch_name=branch_name, episode_commit_id=episode_commit_id,
                                       provider=provider, tenant_id=tenant_id, project_id=project_id)
        resp = self._call(self._stub.ExtractEpisode, req)
        return _run_to_dict(resp.run)

    # ── branching ───────────────────────────────────────────────────
    def create_branch(self, *, branch_name: str, from_branch: str = "", tenant_id: str = "",
                      project_id: str = "") -> dict[str, Any]:
        req = pb.CreateBranchRequest(branch_name=branch_name, from_branch=from_branch,
                                     tenant_id=tenant_id, project_id=project_id)
        resp = self._call(self._stub.CreateBranch, req)
        return {"branch_name": resp.branch_name, "parent_branch_name": resp.parent_branch_name,
                "head_sequence": resp.head_sequence}

    def merge_branch(self, *, source_branch: str, target_branch: str = "", strategy: str = "",
                     tenant_id: str = "", project_id: str = "") -> dict[str, Any]:
        req = pb.MergeBranchRequest(source_branch=source_branch, target_branch=target_branch,
                                    strategy=strategy, tenant_id=tenant_id, project_id=project_id)
        return _commit_to_dict(self._call(self._stub.MergeBranch, req).commit)

    def list_branches(self) -> list[dict[str, Any]]:
        resp = self._call(self._stub.ListBranches, pb.ListBranchesRequest())
        return [{"branch_name": b.branch_name, "parent_branch_name": b.parent_branch_name,
                 "head_sequence": b.head_sequence, "head_commit_id": b.head_commit_id}
                for b in resp.branches]

    # ── maintenance ─────────────────────────────────────────────────
    def set_retention_state(self, *, commit_id: str, retention_state: str, tenant_id: str = "",
                            project_id: str = "") -> dict[str, Any]:
        req = pb.SetRetentionStateRequest(commit_id=commit_id, retention_state=retention_state,
                                          tenant_id=tenant_id, project_id=project_id)
        return _commit_to_dict(self._call(self._stub.SetRetentionState, req).commit)

    def verify_commit_index(self, *, commit_id: str = "", tenant_id: str = "",
                            project_id: str = "") -> list[dict[str, Any]]:
        req = pb.VerifyCommitIndexRequest(commit_id=commit_id, tenant_id=tenant_id,
                                          project_id=project_id)
        resp = self._call(self._stub.VerifyCommitIndex, req)
        return [{"commit_id": i.commit_id, "kind": i.kind, "detail": i.detail}
                for i in resp.issues]
