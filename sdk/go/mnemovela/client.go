package mnemovela

import (
	"context"
	"encoding/json"
)

type Client struct {
	t Transport
}

func New(t Transport) *Client { return &Client{t: t} }

func (c *Client) Close() error { return c.t.Close() }

// Invoke is the low-level escape hatch.
func (c *Client) Invoke(ctx context.Context, method string, params map[string]any) (json.RawMessage, error) {
	return c.t.Invoke(ctx, method, params)
}

type P = map[string]any // convenience alias for params

// writes
func (c *Client) UpsertSubject(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.upsert_subject", p)
}
func (c *Client) UpsertEntity(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.upsert_entity", p)
}
func (c *Client) AddEpisode(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.add_episode", p)
}
func (c *Client) AddFact(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.add_fact", p)
}
func (c *Client) InvalidateFact(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.invalidate_fact", p)
}
func (c *Client) CommitMemory(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.commit_memory", p)
}
func (c *Client) Ingest(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.ingest", p)
}

// queries
func (c *Client) SearchMemory(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.search_memory", p)
}
func (c *Client) QueryMemories(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.query_memories", p)
}
func (c *Client) QueryFacts(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.query_facts", p)
}
func (c *Client) BuildContext(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.build_context", p)
}
func (c *Client) GetContext(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.get_context", p)
}

// resolution / evolution / extraction
func (c *Client) ResolveEntity(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.resolve_entity", p)
}
func (c *Client) ResolveEntityExplained(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.resolve_entity_explained", p)
}
func (c *Client) EvolveEntity(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.evolve_entity", p)
}
func (c *Client) ExtractEpisode(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.extract_episode", p)
}

// branches
func (c *Client) CreateBranch(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.create_branch", p)
}
func (c *Client) MergeBranch(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.merge_branch", p)
}
func (c *Client) ListBranches(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.list_branches", p)
}

// maintenance
func (c *Client) ReconcileRetention(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.reconcile_retention", p)
}
func (c *Client) ReconcileForgetting(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.reconcile_forgetting", p)
}
func (c *Client) RecoverCommit(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.recover_commit", p)
}

// sessions / capture
func (c *Client) SessionStart(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.session_start", p)
}
func (c *Client) SessionEnd(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.session_end", p)
}
func (c *Client) CaptureToolCall(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.capture_tool_call", p)
}
func (c *Client) CaptureDecision(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.capture_decision", p)
}
func (c *Client) CaptureError(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.capture_error", p)
}
func (c *Client) CaptureConstraint(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.capture_constraint", p)
}

// connectors (EE provides implementations)
func (c *Client) SyncConnector(ctx context.Context, p P) (json.RawMessage, error) {
	return c.t.Invoke(ctx, "mnemovela.sync_connector", p)
}
