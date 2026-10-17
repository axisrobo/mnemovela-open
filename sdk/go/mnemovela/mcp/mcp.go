// Package mcp is the MCP (Model Context Protocol) server adapter for the
// Mnemovela SDK. Unlike the transport subpackages (client -> Mnemovela), this
// exposes an MCP host's tool calls to a Mnemovela Client (host -> SDK ->
// Mnemovela). It reuses the shared Client; tools map to `mnemovela.*` methods.
package mcp

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"

	mnemovela "github.com/axisvela/mnemovela-open/sdk/go/v3/mnemovela"
)

// ProtocolVersion is the MCP protocol version this adapter speaks.
const ProtocolVersion = "2024-11-05"

// Request is an MCP (JSON-RPC 2.0) request.
type Request struct {
	JSONRPC string         `json:"jsonrpc"`
	ID      any            `json:"id"`
	Method  string         `json:"method"`
	Params  map[string]any `json:"params"`
}

// Error is a JSON-RPC error object.
type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// Response is an MCP (JSON-RPC 2.0) response.
type Response struct {
	JSONRPC string `json:"jsonrpc"`
	ID      any    `json:"id"`
	Result  any    `json:"result,omitempty"`
	Error   *Error `json:"error,omitempty"`
}

// Tool describes one MCP tool backed by a Mnemovela method.
type Tool struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	InputSchema map[string]any `json:"inputSchema"`
}

// ToolCatalog maps an MCP tool name to a mnemovela.* method + metadata.
var ToolCatalog = []struct {
	Name        string
	Method      string
	Description string
}{
	{"commit_memory", "mnemovela.commit_memory", "Write a memory commit (branch_name, memory_type, payload, metadata, tenant_id, project_id)."},
	{"search_memory", "mnemovela.search_memory", "Hybrid search (branch_name, query, top_k, entity_ids)."},
	{"query_memories", "mnemovela.query_memories", "List commits (branch_name, limit, tenant_id, project_id)."},
	{"add_episode", "mnemovela.add_episode", "Record an episode."},
	{"add_fact", "mnemovela.add_fact", "Add a fact."},
	{"query_facts", "mnemovela.query_facts", "Query facts."},
	{"resolve_entity", "mnemovela.resolve_entity", "Resolve an entity."},
	{"build_context", "mnemovela.build_context", "Build a context bundle."},
	{"create_branch", "mnemovela.create_branch", "Create a branch."},
	{"list_branches", "mnemovela.list_branches", "List branches."},
}

// Tools returns the MCP tool list.
func Tools() []Tool {
	tools := make([]Tool, 0, len(ToolCatalog))
	for _, t := range ToolCatalog {
		tools = append(tools, Tool{
			Name:        t.Name,
			Description: t.Description,
			InputSchema: map[string]any{"type": "object", "additionalProperties": true},
		})
	}
	return tools
}

func methodForTool(name string) (string, bool) {
	for _, t := range ToolCatalog {
		if t.Name == name {
			return t.Method, true
		}
	}
	return "", false
}

// Handle processes one MCP request against client. ok is false for
// notifications (no response) or when there is no client.
func Handle(ctx context.Context, client *mnemovela.Client, req Request) (Response, bool) {
	switch req.Method {
	case "notifications/initialized":
		return Response{}, false
	case "initialize":
		return Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"protocolVersion": ProtocolVersion,
			"serverInfo":      map[string]any{"name": "mnemovela-sdk-go", "version": "0.1.0"},
			"capabilities":    map[string]any{"tools": map[string]any{}},
		}}, true
	case "tools/list":
		return Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"tools": Tools()}}, true
	case "tools/call":
		if client == nil {
			return errResp(req.ID, -32000, "no client"), true
		}
		name, _ := req.Params["name"].(string)
		method, ok := methodForTool(name)
		if !ok {
			return errResp(req.ID, -32602, "unknown tool: "+name), true
		}
		args, _ := req.Params["arguments"].(map[string]any)
		raw, err := client.Invoke(ctx, method, args)
		if err != nil {
			return errResp(req.ID, -32000, err.Error()), true
		}
		// MCP tool results are content blocks; carry the raw JSON as text.
		return Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"content": []map[string]any{{"type": "text", "text": string(raw)}},
			"isError": false,
		}}, true
	default:
		return errResp(req.ID, -32601, "method not found: "+req.Method), true
	}
}

func errResp(id any, code int, msg string) Response {
	return Response{JSONRPC: "2.0", ID: id, Error: &Error{Code: code, Message: msg}}
}

// RunStdio serves MCP over newline-delimited JSON on in/out until EOF.
func RunStdio(ctx context.Context, client *mnemovela.Client, in io.Reader, out io.Writer) error {
	scanner := bufio.NewScanner(in)
	scanner.Buffer(make([]byte, 0, 1<<20), 8<<20)
	enc := json.NewEncoder(out)
	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var req Request
		if err := json.Unmarshal(line, &req); err != nil {
			continue
		}
		resp, ok := Handle(ctx, client, req)
		if !ok {
			continue
		}
		if err := enc.Encode(resp); err != nil {
			return fmt.Errorf("mcp: encode: %w", err)
		}
	}
	return scanner.Err()
}
