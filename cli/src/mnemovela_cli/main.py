from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from mnemovela_client import AsyncMnemovelaHttpClient, MnemovelaClient, MnemovelaError, MnemovelaHttpClient  # noqa: F401


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _identity(args) -> dict[str, str]:
    ident: dict[str, str] = {}
    if args.tenant:
        ident["tenant_id"] = args.tenant
    if args.project:
        ident["project_id"] = args.project
    return ident


# command -> JSON-RPC method (used by the HTTP transport and to document the surface)
_COMMAND_RPC = {
    "add-episode": "mnemovela.add_episode",
    "add-fact": "mnemovela.add_fact",
    "commit": "mnemovela.commit_memory",
    "invalidate-fact": "mnemovela.invalidate_fact",
    "upsert-subject": "mnemovela.upsert_subject",
    "upsert-entity": "mnemovela.upsert_entity",
    "search": "mnemovela.search_memory",
    "query-memories": "mnemovela.query_memories",
    "query-facts": "mnemovela.query_facts",
    "resolve-entity": "mnemovela.resolve_entity",
    "resolve-entity-explained": "mnemovela.resolve_entity_explained",
    "extract-episode": "mnemovela.extract_episode",
    "create-branch": "mnemovela.create_branch",
    "merge-branch": "mnemovela.merge_branch",
    "list-branches": "mnemovela.list_branches",
    "set-retention-state": "mnemovela.set_retention_state",
    "verify-index": "mnemovela.verify_commit_index",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mneme", description="Mnemovela command-line client (gRPC or JSON-RPC/HTTP)")
    p.add_argument("--transport", choices=["grpc", "http"], default="grpc")
    p.add_argument("--address", default="", help="server address (default localhost:9090 grpc, http://localhost:8080 http)")
    p.add_argument("--tenant", default="")
    p.add_argument("--project", default="")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("add-episode"); s.add_argument("--branch", required=True); s.add_argument("--content", required=True)
    s.add_argument("--episode-type", default=""); s.add_argument("--source", default=""); s.add_argument("--observed-at", default="")

    s = sub.add_parser("add-fact"); s.add_argument("--branch", required=True); s.add_argument("--fact-id", required=True)
    s.add_argument("--subject", required=True); s.add_argument("--predicate", required=True); s.add_argument("--object", required=True)
    s.add_argument("--valid-from", default=""); s.add_argument("--valid-to", default=""); s.add_argument("--confidence", type=float, default=0.0)

    s = sub.add_parser("commit"); s.add_argument("--branch", required=True); s.add_argument("--memory-type", required=True)
    s.add_argument("--payload", default="{}", help="JSON object"); s.add_argument("--metadata", default="{}", help="JSON object")
    s.add_argument("--owner-subject-id", default="")

    s = sub.add_parser("invalidate-fact"); s.add_argument("--branch", required=True); s.add_argument("--fact-id", required=True)
    s.add_argument("--invalidated-at", required=True); s.add_argument("--reason", default="")

    s = sub.add_parser("upsert-subject"); s.add_argument("--subject-id", required=True); s.add_argument("--subject-type", required=True)
    s.add_argument("--display-name", default="")

    s = sub.add_parser("upsert-entity"); s.add_argument("--entity-id", required=True); s.add_argument("--entity-type", required=True)
    s.add_argument("--canonical-name", default=""); s.add_argument("--metadata", default="{}")

    s = sub.add_parser("search"); s.add_argument("--branch", required=True); s.add_argument("--query", required=True)
    s.add_argument("--top-k", type=int, default=20); s.add_argument("--entity-id", action="append", default=[])

    s = sub.add_parser("query-memories"); s.add_argument("--branch", required=True); s.add_argument("--entity-id", action="append", default=[]); s.add_argument("--limit", type=int, default=50)

    s = sub.add_parser("query-facts"); s.add_argument("--branch", default=""); s.add_argument("--fact-id", default=""); s.add_argument("--subject", default="")
    s.add_argument("--predicate", default=""); s.add_argument("--true-at", default=""); s.add_argument("--include-invalidated", action="store_true"); s.add_argument("--limit", type=int, default=50)

    s = sub.add_parser("resolve-entity"); s.add_argument("--mention", required=True); s.add_argument("--entity-type", default="")
    s = sub.add_parser("resolve-entity-explained"); s.add_argument("--mention", required=True); s.add_argument("--entity-type", default="")

    s = sub.add_parser("extract-episode"); s.add_argument("--branch", required=True); s.add_argument("--commit", required=True); s.add_argument("--provider", default="")

    s = sub.add_parser("create-branch"); s.add_argument("--name", required=True); s.add_argument("--from", dest="from_branch", default="")
    s = sub.add_parser("merge-branch"); s.add_argument("--source", required=True); s.add_argument("--target", default=""); s.add_argument("--strategy", default="")
    sub.add_parser("list-branches")

    s = sub.add_parser("set-retention-state"); s.add_argument("--commit", required=True); s.add_argument("--state", required=True)
    s = sub.add_parser("verify-index"); s.add_argument("--commit", default="")

    s = sub.add_parser("call", help="invoke any JSON-RPC method (HTTP transport; full surface)")
    s.add_argument("method", help="e.g. mnemovela.build_context")
    s.add_argument("--param", action="append", default=[], metavar="K=V", help="repeatable; value parsed as JSON, else string")
    return p


def _params(args) -> dict[str, Any]:
    """Build the JSON-RPC params for a command from parsed args (used by the HTTP transport)."""
    c = args.command
    p = _identity(args)
    if c == "add-episode":
        p.update(branch_name=args.branch, content=args.content, episode_type=args.episode_type, source=args.source, observed_at=args.observed_at)
    elif c == "add-fact":
        p.update(branch_name=args.branch, fact_id=args.fact_id, subject_id=args.subject, predicate=args.predicate,
                 object_value=args.object, valid_from=args.valid_from, valid_to=args.valid_to, confidence=args.confidence)
    elif c == "commit":
        p.update(branch_name=args.branch, memory_type=args.memory_type, payload=json.loads(args.payload),
                 metadata=json.loads(args.metadata), owner_subject_id=args.owner_subject_id)
    elif c == "invalidate-fact":
        p.update(branch_name=args.branch, fact_id=args.fact_id, invalidated_at=args.invalidated_at, reason=args.reason)
    elif c == "upsert-subject":
        p.update(subject_id=args.subject_id, subject_type=args.subject_type, display_name=args.display_name)
    elif c == "upsert-entity":
        p.update(entity_id=args.entity_id, entity_type=args.entity_type, canonical_name=args.canonical_name, metadata=json.loads(args.metadata))
    elif c == "search":
        p.update(branch_name=args.branch, query=args.query, top_k=args.top_k, entity_ids=args.entity_id)
    elif c == "query-memories":
        p.update(branch_name=args.branch, entity_ids=args.entity_id, limit=args.limit)
    elif c == "query-facts":
        p.update(branch_name=args.branch, fact_id=args.fact_id, subject_id=args.subject, predicate=args.predicate,
                 true_at=args.true_at, include_invalidated=args.include_invalidated, limit=args.limit)
    elif c in ("resolve-entity", "resolve-entity-explained"):
        p.update(mention=args.mention, entity_type=args.entity_type)
    elif c == "extract-episode":
        p.update(branch_name=args.branch, episode_commit_id=args.commit, provider=args.provider)
    elif c == "create-branch":
        p.update(branch_name=args.name, from_branch=args.from_branch)
    elif c == "merge-branch":
        p.update(source_branch=args.source, target_branch=args.target, strategy=args.strategy)
    elif c == "set-retention-state":
        p.update(commit_id=args.commit, retention_state=args.state)
    elif c == "verify-index":
        p.update(commit_id=args.commit)
    # list-branches: no extra params
    return p


def _dispatch_grpc(args, client: MnemovelaClient) -> Any:
    ident = _identity(args)
    c = args.command
    if c == "add-episode":
        return client.add_episode(branch_name=args.branch, content=args.content, episode_type=args.episode_type,
                                  source=args.source, observed_at=args.observed_at, **ident)
    if c == "add-fact":
        return client.add_fact(branch_name=args.branch, fact_id=args.fact_id, subject_id=args.subject,
                               predicate=args.predicate, object_value=args.object, valid_from=args.valid_from,
                               valid_to=args.valid_to, confidence=args.confidence, **ident)
    if c == "commit":
        return client.commit_memory(branch_name=args.branch, memory_type=args.memory_type,
                                    payload=json.loads(args.payload), metadata=json.loads(args.metadata),
                                    owner_subject_id=args.owner_subject_id, **ident)
    if c == "invalidate-fact":
        return client.invalidate_fact(branch_name=args.branch, fact_id=args.fact_id,
                                      invalidated_at=args.invalidated_at, reason=args.reason, **ident)
    if c == "upsert-subject":
        return client.upsert_subject(subject_id=args.subject_id, subject_type=args.subject_type,
                                     display_name=args.display_name, **ident)
    if c == "upsert-entity":
        return client.upsert_entity(entity_id=args.entity_id, entity_type=args.entity_type,
                                    canonical_name=args.canonical_name, metadata=json.loads(args.metadata), **ident)
    if c == "search":
        return client.search_memory(args.branch, args.query, top_k=args.top_k, entity_ids=args.entity_id)
    if c == "query-memories":
        return client.query_memories(branch_name=args.branch, entity_ids=args.entity_id, limit=args.limit, **ident)
    if c == "query-facts":
        return client.query_facts(branch_name=args.branch, fact_id=args.fact_id, subject_id=args.subject,
                                  predicate=args.predicate, true_at=args.true_at,
                                  include_invalidated=args.include_invalidated, limit=args.limit, **ident)
    if c == "resolve-entity":
        return client.resolve_entity(mention=args.mention, entity_type=args.entity_type, **ident)
    if c == "resolve-entity-explained":
        return client.resolve_entity_explained(mention=args.mention, entity_type=args.entity_type, **ident)
    if c == "extract-episode":
        return client.extract_episode(branch_name=args.branch, episode_commit_id=args.commit, provider=args.provider, **ident)
    if c == "create-branch":
        return client.create_branch(branch_name=args.name, from_branch=args.from_branch, **ident)
    if c == "merge-branch":
        return client.merge_branch(source_branch=args.source, target_branch=args.target, strategy=args.strategy, **ident)
    if c == "list-branches":
        return client.list_branches()
    if c == "set-retention-state":
        return client.set_retention_state(commit_id=args.commit, retention_state=args.state, **ident)
    if c == "verify-index":
        return client.verify_commit_index(commit_id=args.commit, **ident)
    if c == "call":
        raise SystemExit("the 'call' command requires --transport http")
    raise SystemExit(f"unknown command: {c}")


def _parse_call_params(items: list[str]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"bad --param {item!r} (want K=V)")
        try:
            params[key] = json.loads(value)
        except json.JSONDecodeError:
            params[key] = value
    return params


def _dispatch_http(args, client: MnemovelaHttpClient) -> Any:
    if args.command == "call":
        params = _identity(args)
        params.update(_parse_call_params(args.param))
        return client.call(args.method, **params)
    return client.call(_COMMAND_RPC[args.command], **_params(args))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    address = args.address or ("http://localhost:8080" if args.transport == "http" else "localhost:9090")
    try:
        if args.transport == "http":
            client = MnemovelaHttpClient(address)
            _print(_dispatch_http(args, client))
        else:
            with MnemovelaClient(address) as client:
                _print(_dispatch_grpc(args, client))
        return 0
    except MnemovelaError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
