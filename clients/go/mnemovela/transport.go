package mnemovela

import (
	"context"
	"encoding/json"
)

// Transport invokes a Mnemovela method with JSON-object params and returns the raw
// JSON result (object or array). Implementations: JSON-RPC over HTTP, and gRPC.
type Transport interface {
	Invoke(ctx context.Context, method string, params map[string]any) (json.RawMessage, error)
	Close() error
}
