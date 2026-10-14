package mnemovela

import "context"

// TokenSource yields a bearer token presented to Mnemovela (e.g. a short-lived
// AEGIVELA workload-assertion JWT). Transports apply it per call: as an
// `Authorization: Bearer <token>` HTTP header (JSON-RPC) or as gRPC metadata.
type TokenSource interface {
	Token(ctx context.Context) (string, error)
}

type staticTokenSource string

func (s staticTokenSource) Token(context.Context) (string, error) { return string(s), nil }

// StaticTokenSource returns a TokenSource with a fixed token.
func StaticTokenSource(token string) TokenSource { return staticTokenSource(token) }
