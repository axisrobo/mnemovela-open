package mnemovela

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync/atomic"
)

type JSONRPCTransport struct {
	url    string
	client *http.Client
	id     atomic.Int64
}

func NewJSONRPCTransport(baseURL string) *JSONRPCTransport {
	return &JSONRPCTransport{url: strings.TrimRight(baseURL, "/") + "/api/v1/jsonrpc", client: http.DefaultClient}
}

func (t *JSONRPCTransport) Close() error { return nil }

func (t *JSONRPCTransport) Invoke(ctx context.Context, method string, params map[string]any) (json.RawMessage, error) {
	if params == nil {
		params = map[string]any{}
	}
	reqBody, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": t.id.Add(1), "method": method, "params": params})
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, t.url, bytes.NewReader(reqBody))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("content-type", "application/json")
	resp, err := t.client.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, &MnemeError{Code: resp.StatusCode, Message: fmt.Sprintf("HTTP %d", resp.StatusCode)}
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
		return nil, &MnemeError{Code: out.Error.Code, Message: out.Error.Message}
	}
	return out.Result, nil
}
