package grpc

import (
	"context"
	"encoding/json"
	"net"
	"testing"

	pb "github.com/axisvela/mnemovela-open/sdk/go/v3/internal/mnemovelav1"
	mnemovela "github.com/axisvela/mnemovela-open/sdk/go/v3/mnemovela"
	"google.golang.org/grpc"
)

type fakeServer struct {
	pb.UnimplementedMnemovelaServer
}

func (fakeServer) AddEpisode(_ context.Context, req *pb.AddEpisodeRequest) (*pb.AddEpisodeResponse, error) {
	return &pb.AddEpisodeResponse{Commit: &pb.Commit{CommitId: "mem_1", BranchName: req.BranchName, MemoryType: "episode"}}, nil
}
func (fakeServer) ListBranches(context.Context, *pb.ListBranchesRequest) (*pb.ListBranchesResponse, error) {
	return &pb.ListBranchesResponse{Branches: []*pb.ListBranchesResponse_Branch{{BranchName: "main", HeadSequence: 3}}}, nil
}

func startFakeGRPC(t *testing.T) (addr string, stop func()) {
	t.Helper()
	lis, err := net.Listen("tcp", "localhost:0")
	if err != nil {
		t.Fatal(err)
	}
	s := grpc.NewServer()
	pb.RegisterMnemovelaServer(s, fakeServer{})
	go func() { _ = s.Serve(lis) }()
	return lis.Addr().String(), s.Stop
}

func TestGRPCAddEpisode(t *testing.T) {
	addr, stop := startFakeGRPC(t)
	defer stop()
	tr, err := New(addr)
	if err != nil {
		t.Fatal(err)
	}
	c := mnemovela.New(tr)
	defer c.Close()
	raw, err := c.AddEpisode(context.Background(), mnemovela.P{"branch_name": "main", "content": "hi"})
	if err != nil {
		t.Fatal(err)
	}
	var m map[string]any
	_ = json.Unmarshal(raw, &m)
	commit := m["commit"].(map[string]any)
	if commit["commit_id"] != "mem_1" {
		t.Fatalf("commit_id = %v", commit["commit_id"])
	}
}

func TestGRPCUnsupportedMethod(t *testing.T) {
	addr, stop := startFakeGRPC(t)
	defer stop()
	tr, _ := New(addr)
	c := mnemovela.New(tr)
	defer c.Close()
	_, err := c.BuildContext(context.Background(), nil) // not in proto
	if _, ok := err.(*mnemovela.MnemeError); !ok {
		t.Fatalf("expected MnemeError for unsupported method, got %v", err)
	}
}
