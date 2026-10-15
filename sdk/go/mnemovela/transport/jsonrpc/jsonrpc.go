// Package jsonrpc is the JSON-RPC-over-HTTP transport for the Mnemovela SDK
// (POST /api/v1/jsonrpc). It is one of two Transport implementations; the
// shared Client/Transport/MnemeError/TokenSource live in package mnemovela.
package jsonrpc

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync/atomic"

	mnemovela "github.com/axisrobo/mnemovela-open/sdk/go/mnemovela"
)

// Transport speaks JSON-RPC 2.0 over HTTP.
type Transport struct {
	url    string
	client *http.Client
	id     atomic.Int64
	tokens mnemovela.TokenSource
}

// New creates a JSON-RPC transport for baseURL.
func New(baseURL string) *Transport {
	return &Transport{url: strings.TrimRight(baseURL, "/") + "/api/v1/jsonrpc", client: http.DefaultClient}
}

// NewWithToken builds a transport that presents a bearer token on every call.
func NewWithToken(baseURL string, ts mnemovela.TokenSource) *Transport {
	t := New(baseURL)
	t.tokens = ts
	return t
}

// SetTokenSource sets (or clears) the credential source.
func (t *Transport) SetTokenSource(ts mnemovela.TokenSource) { t.tokens = ts }

// Close releases resources (no-op for HTTP).
func (t *Transport) Close() error { return nil }

// Invoke performs one JSON-RPC call.
func (t *Transport) Invoke(ctx context.Context, method string, params map[string]any) (json.RawMessage, error) {
	if params == nil {
		params = map[string]any{}
	}
	reqBody, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": t.id.Add(1), "method": method, "params": params})
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, t.url, bytes.NewReader(reqBody))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("content-type", "application/json")
	if t.tokens != nil {
		tok, err := t.tokens.Token(ctx)
		if err != nil {
			return nil, err
		}
		if tok != "" {
			httpReq.Header.Set("Authorization", "Bearer "+tok)
		}
	}
	resp, err := t.client.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, &mnemovela.MnemeError{Code: resp.StatusCode, Message: fmt.Sprintf("HTTP %d", resp.StatusCode)}
	}
	var out struct {
		Result json.RawMessage `json:"result"`
		Error  *struct {
			Code    int    `json:"code"`
			Message string `json:"message"`
		} `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	if out.Error != nil {
		return nil, &mnemovela.MnemeError{Code: out.Error.Code, Message: out.Error.Message}
	}
	return out.Result, nil
}
