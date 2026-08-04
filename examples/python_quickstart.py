"""End-to-end Mnemovela quickstart against a running server (JSON-RPC over HTTP).

Start a server first, e.g. `mnemovela-http` (default 127.0.0.1:8080), then:

    python python_quickstart.py --address http://127.0.0.1:8080

Uses the full method surface via MnemeHttpClient. No engine code is imported;
this talks to the server purely over HTTP.
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Mnemovela HTTP quickstart")
    parser.add_argument("--address", default="http://127.0.0.1:8080")
    parser.add_argument("--branch", default="main")
    args = parser.parse_args()

    from mnemovela_client import MnemeHttpClient, MnemeError

    client = MnemeHttpClient(args.address)

    try:
        # 1) Seed a few episodes that build up a small story over time.
        episodes = [
            "Monday: kickoff meeting confirmed the project scope.",
            "Tuesday: raised ambiguity in contract clause 7 about arbitration.",
            "Wednesday: Team B proposed arbitration in Singapore.",
            "Thursday: agreed to standardize the clause-7 negotiation procedure.",
        ]
        for text in episodes:
            commit = client.add_episode(branch_name=args.branch, content=text)
            print(f"add_episode -> {commit.get('commit_id')}: {text[:40]}...")

        # 2) Hybrid search over the accrued memory.
        results = client.search_memory(branch_name=args.branch, query="clause 7 arbitration", top_k=5)
        print(f"\nsearch_memory -> {len(results)} result(s)")

        # 3) Assemble task context (full-surface method; not available over gRPC).
        context = client.build_context(query="What was decided about clause 7?", branch_name=args.branch, budget=800)
        sections = context.get("sections") if isinstance(context, dict) else None
        print(f"build_context -> {len(sections) if sections is not None else 'n/a'} section(s)")

        # 4) Branches.
        branches = client.list_branches()
        print("list_branches ->", [b.get("branch_name") for b in branches] if isinstance(branches, list) else branches)

        print("\nOK")
        return 0
    except MnemeError as err:
        print(f"Mnemovela error: {err}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
