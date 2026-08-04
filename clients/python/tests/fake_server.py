from __future__ import annotations

import contextlib
from concurrent import futures

import grpc

from mnemovela_client._generated import mnemovela_v1_pb2 as pb
from mnemovela_client._generated import mnemovela_v1_pb2_grpc as pb_grpc


class FakeMneme(pb_grpc.MnemeServicer):
    def AddEpisode(self, request, context):
        c = pb.Commit(commit_id="mem_1", branch_name=request.branch_name, memory_type="episode")
        c.payload["content"].string_value = request.content
        return pb.AddEpisodeResponse(commit=c)

    def AddFact(self, request, context):
        c = pb.Commit(commit_id="mem_2", branch_name=request.branch_name, memory_type="fact")
        return pb.AddFactResponse(commit=c)

    def CommitMemory(self, request, context):
        c = pb.Commit(commit_id="mem_3", branch_name=request.branch_name, memory_type=request.memory_type)
        for k, v in request.payload.items():
            c.payload[k].CopyFrom(v)
        return pb.CommitMemoryResponse(commit=c)

    def InvalidateFact(self, request, context):
        c = pb.Commit(commit_id="mem_4", branch_name=request.branch_name, memory_type="fact")
        return pb.InvalidateFactResponse(commit=c)

    def UpsertSubject(self, request, context):
        return pb.UpsertSubjectResponse(subject_id=request.subject_id or "s1")

    def UpsertEntity(self, request, context):
        return pb.UpsertEntityResponse(entity_id=request.entity_id or "e1")

    def SearchMemory(self, request, context):
        resp = pb.SearchMemoryResponse()
        r1 = resp.results.add(); r1.score = 0.9; r1.commit.commit_id = "mem_1"
        r2 = resp.results.add(); r2.score = 0.5; r2.commit.commit_id = "mem_2"
        return resp

    def QueryMemories(self, request, context):
        resp = pb.QueryMemoriesResponse()
        c = resp.commits.add(); c.commit_id = "mem_1"; c.branch_name = request.branch_name
        return resp

    def QueryFacts(self, request, context):
        resp = pb.QueryFactsResponse()
        f = resp.facts.add(); f.fact_id = "f1"; f.subject_id = request.subject_id or "s1"
        return resp

    def ResolveEntity(self, request, context):
        return pb.ResolveEntityResponse(entity_id="e1", entity_type=request.entity_type,
                                        canonical_name=request.mention)

    def ResolveEntityExplained(self, request, context):
        resp = pb.ResolveEntityExplainedResponse(matched=True, match_type="exact",
                                                  matched_value=request.mention, confidence=1.0)
        resp.entity.entity_id = "e1"
        resp.entity.entity_type = request.entity_type
        resp.entity.canonical_name = request.mention
        return resp

    def ExtractEpisode(self, request, context):
        resp = pb.ExtractEpisodeResponse()
        resp.run.run_id = "run_1"
        resp.run.episode_commit_id = request.episode_commit_id
        resp.run.branch_name = request.branch_name
        resp.run.status = "extracted"
        return resp

    def CreateBranch(self, request, context):
        return pb.CreateBranchResponse(branch_name=request.branch_name, parent_branch_name=request.from_branch)

    def MergeBranch(self, request, context):
        c = pb.Commit(commit_id="mem_5", branch_name=request.target_branch, memory_type="merge")
        return pb.MergeBranchResponse(commit=c)

    def ListBranches(self, request, context):
        resp = pb.ListBranchesResponse()
        b = resp.branches.add(); b.branch_name = "main"; b.head_sequence = 3
        return resp

    def SetRetentionState(self, request, context):
        c = pb.Commit(commit_id=request.commit_id, retention_state=request.retention_state)
        return pb.SetRetentionStateResponse(commit=c)

    def VerifyCommitIndex(self, request, context):
        resp = pb.VerifyCommitIndexResponse()
        i = resp.issues.add(); i.commit_id = request.commit_id or "mem_1"; i.kind = "ok"; i.detail = ""
        return resp


@contextlib.contextmanager
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb_grpc.add_MnemeServicer_to_server(FakeMneme(), server)
    port = server.add_insecure_port("localhost:0")
    server.start()
    try:
        yield f"localhost:{port}"
    finally:
        server.stop(None)
