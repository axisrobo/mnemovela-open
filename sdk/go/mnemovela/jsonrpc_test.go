package mnemovela

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func fakeRPCServer() *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			ID     any            `json:"id"`
			Method string         `json:"method"`
			Params map[string]any `json:"params"`
		}
		_ = json.NewDecoder(r.Body).Decode(&req)
		w.Header().Set("content-type", "application/json")
		switch req.Method {
		case "mnemovela.add_episode":
			json.NewEncoder(w).Encode(map[string]any{"jsonrpc": "2.0", "id": req.ID,
				"result": map[string]any{"commit_id": "mem_1", "branch_name": req.Params["branch_name"]}})
		case "mnemovela.search_memory":
			json.NewEncoder(w).Encode(map[string]any{"jsonrpc": "2.0", "id": req.ID,
				"result": []any{map[string]any{"score": 0.9}, map[string]any{"score": 0.5}}})
		default:
			json.NewEncoder(w).Encode(map[string]any{"jsonrpc": "2.0", "id": req.ID,
				"error": map[string]any{"code": -32601, "message": "method not found"}})
		}
	}))
}

func TestJSONRPCAddEpisode(t *testing.T) {
	srv := fakeRPCServer()
	defer srv.Close()
	c := New(NewJSONRPCTransport(srv.URL))
	defer c.Close()
	raw, err := c.AddEpisode(context.Background(), P{"branch_name": "main", "content": "hi"})
	if err != nil {
		t.Fatal(err)
	}
	var m map[string]any
	_ = json.Unmarshal(raw, &m)
	if m["commit_id"] != "mem_1" {
		t.Fatalf("commit_id = %v", m["commit_id"])
	}
}

func TestJSONRPCUnknownMethodError(t *testing.T) {
	srv := fakeRPCServer()
	defer srv.Close()
	c := New(NewJSONRPCTransport(srv.URL))
	defer c.Close()
	_, err := c.Invoke(context.Background(), "mnemovela.nope", nil)
	me, ok := err.(*MnemeError)
	if !ok || me.Code != -32601 {
		t.Fatalf("expected -32601 MnemeError, got %v", err)
	}
}
