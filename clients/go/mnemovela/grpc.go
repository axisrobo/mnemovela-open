package mnemovela

import (
	"context"
	"encoding/json"

	pb "github.com/axisrobo/mnemovela-open/clients/go/internal/mnemovelav1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
)

type grpcMethodSpec struct {
	newReq func() proto.Message
	call   func(ctx context.Context, stub pb.MnemovelaClient, req proto.Message) (proto.Message, error)
}

type GRPCTransport struct {
	conn *grpc.ClientConn
	stub pb.MnemovelaClient
}

func NewGRPCTransport(addr string) (*GRPCTransport, error) {
	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}
	return &GRPCTransport{conn: conn, stub: pb.NewMnemovelaClient(conn)}, nil
}

func (t *GRPCTransport) Close() error { return t.conn.Close() }

func (t *GRPCTransport) Invoke(ctx context.Context, method string, params map[string]any) (json.RawMessage, error) {
	spec, ok := grpcMethods[method]
	if !ok {
		return nil, &MnemeError{Code: -32601, Message: "method not supported over gRPC: " + method}
	}
	if params == nil {
		params = map[string]any{}
	}
	reqJSON, _ := json.Marshal(params)
	req := spec.newReq()
	if err := protojson.Unmarshal(reqJSON, req); err != nil {
		return nil, &MnemeError{Code: -32602, Message: err.Error()}
	}
	resp, err := spec.call(ctx, t.stub, req)
	if err != nil {
		return nil, &MnemeError{Code: -32000, Message: err.Error()}
	}
	out, err := protojson.MarshalOptions{UseProtoNames: true}.Marshal(resp)
	if err != nil {
		return nil, err
	}
	return out, nil
}

var grpcMethods = map[string]grpcMethodSpec{
	// --- typed writes ---
	"mnemovela.commit_memory": {
		newReq: func() proto.Message { return &pb.CommitMemoryRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.CommitMemory(ctx, r.(*pb.CommitMemoryRequest))
		},
	},
	"mnemovela.add_episode": {
		newReq: func() proto.Message { return &pb.AddEpisodeRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.AddEpisode(ctx, r.(*pb.AddEpisodeRequest))
		},
	},
	"mnemovela.add_fact": {
		newReq: func() proto.Message { return &pb.AddFactRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.AddFact(ctx, r.(*pb.AddFactRequest))
		},
	},
	"mnemovela.invalidate_fact": {
		newReq: func() proto.Message { return &pb.InvalidateFactRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.InvalidateFact(ctx, r.(*pb.InvalidateFactRequest))
		},
	},
	"mnemovela.upsert_subject": {
		newReq: func() proto.Message { return &pb.UpsertSubjectRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.UpsertSubject(ctx, r.(*pb.UpsertSubjectRequest))
		},
	},
	"mnemovela.upsert_entity": {
		newReq: func() proto.Message { return &pb.UpsertEntityRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.UpsertEntity(ctx, r.(*pb.UpsertEntityRequest))
		},
	},
	// --- queries ---
	"mnemovela.search_memory": {
		newReq: func() proto.Message { return &pb.SearchMemoryRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.SearchMemory(ctx, r.(*pb.SearchMemoryRequest))
		},
	},
	"mnemovela.query_memories": {
		newReq: func() proto.Message { return &pb.QueryMemoriesRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.QueryMemories(ctx, r.(*pb.QueryMemoriesRequest))
		},
	},
	"mnemovela.query_facts": {
		newReq: func() proto.Message { return &pb.QueryFactsRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.QueryFacts(ctx, r.(*pb.QueryFactsRequest))
		},
	},
	// --- resolution ---
	"mnemovela.resolve_entity": {
		newReq: func() proto.Message { return &pb.ResolveEntityRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.ResolveEntity(ctx, r.(*pb.ResolveEntityRequest))
		},
	},
	"mnemovela.resolve_entity_explained": {
		newReq: func() proto.Message { return &pb.ResolveEntityExplainedRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.ResolveEntityExplained(ctx, r.(*pb.ResolveEntityExplainedRequest))
		},
	},
	// --- extraction ---
	"mnemovela.extract_episode": {
		newReq: func() proto.Message { return &pb.ExtractEpisodeRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.ExtractEpisode(ctx, r.(*pb.ExtractEpisodeRequest))
		},
	},
	// --- branching ---
	"mnemovela.create_branch": {
		newReq: func() proto.Message { return &pb.CreateBranchRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.CreateBranch(ctx, r.(*pb.CreateBranchRequest))
		},
	},
	"mnemovela.merge_branch": {
		newReq: func() proto.Message { return &pb.MergeBranchRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.MergeBranch(ctx, r.(*pb.MergeBranchRequest))
		},
	},
	"mnemovela.list_branches": {
		newReq: func() proto.Message { return &pb.ListBranchesRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.ListBranches(ctx, r.(*pb.ListBranchesRequest))
		},
	},
	// --- maintenance ---
	"mnemovela.set_retention_state": {
		newReq: func() proto.Message { return &pb.SetRetentionStateRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.SetRetentionState(ctx, r.(*pb.SetRetentionStateRequest))
		},
	},
	"mnemovela.verify_commit_index": {
		newReq: func() proto.Message { return &pb.VerifyCommitIndexRequest{} },
		call: func(ctx context.Context, s pb.MnemovelaClient, r proto.Message) (proto.Message, error) {
			return s.VerifyCommitIndex(ctx, r.(*pb.VerifyCommitIndexRequest))
		},
	},
}
