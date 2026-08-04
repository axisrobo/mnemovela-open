#!/usr/bin/env bash
# end-to-end-example.sh — a scripted walkthrough of one agent session with Mnemovela.
#
# Prerequisites: mnemovela-mcp-stdio (or mnemovela-jsonrpc-stdio) on PATH.
# Start the server in a separate terminal first: mnemovela-mcp-stdio
#
# This example uses curl against the HTTP JSON-RPC endpoint for readability.
# In a real agent session, the MCP tools are called directly.

SERVER="${MNEMOVELA_ADDR:-http://127.0.0.1:8080}"
RPC="${SERVER}/api/v1/jsonrpc"

call() {
  local method="$1" params="$2"
  curl -s -X POST "$RPC" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$method\",\"params\":$params}" \
    | python3 -m json.tool 2>/dev/null || true
}

echo "=== 1. Session start — recall project state ==="
call "mnemovela.search_memory" '{"query":"current project state constraints","top_k":5}'

echo ""
echo "=== 2. Start work — register a new module entity ==="
call "mnemovela.upsert_entity" '{"entity_id":"module:auth-middleware","entity_type":"module","canonical_name":"Auth middleware"}'

echo ""
echo "=== 3. Capture a design decision ==="
call "mnemovela.capture_decision" '{"decision_summary":"Use JWT for session tokens","rationale":"Stateless, no DB lookup per request","alternatives":"Opaque session tokens with Redis lookup"}'

echo ""
echo "=== 4. Store a durable fact about the module ==="
call "mnemovela.add_fact" '{"branch_name":"main","fact_id":"fact:auth-uses-jwt","subject_id":"module:auth-middleware","predicate":"implements","object_value":"JWT-based session authentication"}'

echo ""
echo "=== 5. Store a project constraint ==="
call "mnemovela.capture_constraint" '{"constraint_summary":"JWT secrets must never be hardcoded or committed — always from env or a secrets manager","branch_name":"main"}'

echo ""
echo "=== 6. Later session — recall what we know about auth ==="
call "mnemovela.search_memory" '{"query":"auth middleware JWT session","top_k":5}'
call "mnemovela.query_facts" '{"subject_id":"module:auth-middleware"}'

echo ""
echo "=== 7. Session end — write summary ==="
call "mnemovela.session_end" '{"summary":"Scaffolded auth middleware with JWT tokens. Registered module entity. Captured design decision and security constraint.","changed_files":"[\"src/auth/middleware.ts\",\"src/auth/tokens.ts\"]","decisions":"[\"JWT over opaque tokens\"]","branch_name":"main"}'

echo ""
echo "=== Done. Run the same recall queries in the next session to see the accumulated memory. ==="
