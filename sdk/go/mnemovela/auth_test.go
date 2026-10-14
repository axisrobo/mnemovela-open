package mnemovela

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestJSONRPCAuthHeader(t *testing.T) {
	var gotAuth string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"jsonrpc":"2.0","id":1,"result":{}}`))
	}))
	defer srv.Close()

	c := New(NewJSONRPCTransportWithToken(srv.URL, StaticTokenSource("tok-1")))
	if _, err := c.CommitMemory(context.Background(), P{"branch_name": "main", "memory_type": "event"}); err != nil {
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

	c := New(NewJSONRPCTransport(srv.URL))
	_, _ = c.CommitMemory(context.Background(), P{"branch_name": "main", "memory_type": "event"})
	if gotAuth != "" {
		t.Fatalf("auth = %q, want empty", gotAuth)
	}
}
