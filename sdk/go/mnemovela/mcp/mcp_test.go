package mcp

import (
	"context"
	"encoding/json"
	"testing"

	mnemovela "github.com/axisrobo/mnemovela-open/sdk/go/mnemovela"
)

type fakeTransport struct {
	lastMethod string
	lastParams map[string]any
}

func (f *fakeTransport) Invoke(_ context.Context, method string, params map[string]any) (json.RawMessage, error) {
	f.lastMethod, f.lastParams = method, params
	return json.RawMessage(`{"ok":true}`), nil
}
func (f *fakeTransport) Close() error { return nil }

func TestHandleInitializeAndToolsList(t *testing.T) {
	c := mnemovela.New(&fakeTransport{})
	init, ok := Handle(context.Background(), c, Request{JSONRPC: "2.0", ID: 1, Method: "initialize"})
	if !ok || init.Result == nil {
		t.Fatalf("initialize = %+v", init)
	}
	list, ok := Handle(context.Background(), c, Request{JSONRPC: "2.0", ID: 2, Method: "tools/list"})
	if !ok {
		t.Fatal("tools/list not ok")
	}
	tools, _ := list.Result.(map[string]any)["tools"].([]Tool)
	if len(tools) == 0 {
		t.Fatal("expected tools")
	}
}

func TestHandleToolsCall(t *testing.T) {
	ft := &fakeTransport{}
	c := mnemovela.New(ft)
	resp, ok := Handle(context.Background(), c, Request{
		JSONRPC: "2.0", ID: 3, Method: "tools/call",
		Params: map[string]any{"name": "commit_memory", "arguments": map[string]any{"branch_name": "main"}},
	})
	if !ok || resp.Error != nil {
		t.Fatalf("tools/call = %+v", resp)
	}
	if ft.lastMethod != "mnemovela.commit_memory" {
		t.Fatalf("method = %s", ft.lastMethod)
	}
}

func TestHandleNotificationNoResponse(t *testing.T) {
	c := mnemovela.New(&fakeTransport{})
	if _, ok := Handle(context.Background(), c, Request{Method: "notifications/initialized"}); ok {
		t.Fatal("notification should not produce a response")
	}
}
