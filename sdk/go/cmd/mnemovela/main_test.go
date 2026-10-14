package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func fakeRPC() *httptest.Server {
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
		case "mnemovela.list_branches":
			json.NewEncoder(w).Encode(map[string]any{"jsonrpc": "2.0", "id": req.ID,
				"result": []any{map[string]any{"branch_name": "main"}}})
		default:
			json.NewEncoder(w).Encode(map[string]any{"jsonrpc": "2.0", "id": req.ID,
				"error": map[string]any{"code": -32601, "message": "method not found"}})
		}
	}))
}

func TestCLIAddEpisodeHTTP(t *testing.T) {
	srv := fakeRPC()
	defer srv.Close()
	var out bytes.Buffer
	rc := run([]string{"--transport", "http", "--address", srv.URL, "add-episode", "--branch-name", "main", "--content", "hi"}, &out)
	if rc != 0 {
		t.Fatalf("rc=%d out=%s", rc, out.String())
	}
	var m map[string]any
	if err := json.Unmarshal(out.Bytes(), &m); err != nil {
		t.Fatalf("bad json: %s", out.String())
	}
	if m["commit_id"] != "mem_1" {
		t.Fatalf("commit_id=%v", m["commit_id"])
	}
}

func TestCLIListBranchesHTTP(t *testing.T) {
	srv := fakeRPC()
	defer srv.Close()
	var out bytes.Buffer
	rc := run([]string{"--transport", "http", "--address", srv.URL, "list-branches"}, &out)
	if rc != 0 {
		t.Fatalf("rc=%d", rc)
	}
	if !bytes.Contains(out.Bytes(), []byte("main")) {
		t.Fatalf("out=%s", out.String())
	}
}

func TestCLIUnknownCommand(t *testing.T) {
	var out bytes.Buffer
	rc := run([]string{"bogus"}, &out)
	if rc == 0 {
		t.Fatal("expected nonzero rc for unknown command")
	}
}
