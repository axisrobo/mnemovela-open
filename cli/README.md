# Mnemovela CLI (`mnemovela`)

Command-line client for a running Mnemovela server (gRPC). Wraps `mnemovela-client`.

```bash
pip install mnemovela-cli
mnemovela --address localhost:9090 add-episode --branch main --content "hello"
mnemovela search --branch main --query "hello" --top-k 5
mnemovela list-branches
```

All commands print JSON. Global flags: `--address` (default `localhost:9090`),
`--tenant`, `--project`. Surface is the 17 Mnemovela gRPC RPCs.
