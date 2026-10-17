package jsonrpc

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	mnemovela "github.com/axisvela/mnemovela-open/sdk/go/mnemovela"
)

func TestJSONRPCAuthHeader(t *testing.T) {
	var gotAuth string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"jsonrpc":"2.0","id":1,"result":{}}`))
	}))
	defer srv.Close()

	c := mnemovela.New(NewWithToken(srv.URL, mnemovela.StaticTokenSource("tok-1")))
	if _, err := c.CommitMemory(context.Background(), mnemovela.P{"branch_name": "main", "memory_type": "event"}); err != nil {
		t.Fatalf("CommitMemory: %v", err)
	}
	if gotAuth != "Bearer tok-1" {
		t.Fatalf("auth = %q, want Bearer tok-1", gotAuth)
	}
}

func TestJSONRPCNoAuthWhenUnset(t *testing.T) {
	var gotAuth string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"jsonrpc":"2.0","id":1,"result":{}}`))
	}))
	defer srv.Close()

	c := mnemovela.New(New(srv.URL))
	_, _ = c.CommitMemory(context.Background(), mnemovela.P{"branch_name": "main", "memory_type": "event"})
	if gotAuth != "" {
		t.Fatalf("auth = %q, want empty", gotAuth)
	}
}
