package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/axisrobo/mnemovela-open/clients/go/mnemovela"
)

type cmdSpec struct {
	rpc   string
	strs  []string
	ints  []string
	flts  []string
	bools []string
	jsons []string // parsed as JSON objects (e.g. payload, metadata)
}

var commands = map[string]cmdSpec{
	"add-episode":              {rpc: "mnemovela.add_episode", strs: []string{"branch-name", "content", "episode-type", "source", "observed-at"}},
	"add-fact":                 {rpc: "mnemovela.add_fact", strs: []string{"branch-name", "fact-id", "subject-id", "predicate", "object-value", "valid-from", "valid-to"}, flts: []string{"confidence"}},
	"commit":                   {rpc: "mnemovela.commit_memory", strs: []string{"branch-name", "memory-type", "owner-subject-id"}, jsons: []string{"payload", "metadata"}},
	"invalidate-fact":          {rpc: "mnemovela.invalidate_fact", strs: []string{"branch-name", "fact-id", "invalidated-at", "reason"}},
	"upsert-subject":           {rpc: "mnemovela.upsert_subject", strs: []string{"subject-id", "subject-type", "display-name"}},
	"upsert-entity":            {rpc: "mnemovela.upsert_entity", strs: []string{"entity-id", "entity-type", "canonical-name"}},
	"search":                   {rpc: "mnemovela.search_memory", strs: []string{"branch-name", "query"}, ints: []string{"top-k"}},
	"query-memories":           {rpc: "mnemovela.query_memories", strs: []string{"branch-name"}, ints: []string{"limit"}},
	"query-facts":              {rpc: "mnemovela.query_facts", strs: []string{"branch-name", "fact-id", "subject-id", "predicate", "true-at"}, ints: []string{"limit"}, bools: []string{"include-invalidated"}},
	"resolve-entity":           {rpc: "mnemovela.resolve_entity", strs: []string{"mention", "entity-type"}},
	"resolve-entity-explained": {rpc: "mnemovela.resolve_entity_explained", strs: []string{"mention", "entity-type"}},
	"extract-episode":          {rpc: "mnemovela.extract_episode", strs: []string{"branch-name", "episode-commit-id", "provider"}},
	"create-branch":            {rpc: "mnemovela.create_branch", strs: []string{"branch-name", "from-branch"}},
	"merge-branch":             {rpc: "mnemovela.merge_branch", strs: []string{"source-branch", "target-branch", "strategy"}},
	"list-branches":            {rpc: "mnemovela.list_branches"},
	"set-retention-state":      {rpc: "mnemovela.set_retention_state", strs: []string{"commit-id", "retention-state"}},
	"verify-index":             {rpc: "mnemovela.verify_commit_index", strs: []string{"commit-id"}},
}

func kebabToSnake(s string) string { return strings.ReplaceAll(s, "-", "_") }

func run(args []string, out io.Writer) int {
	global := flag.NewFlagSet("mnemovela", flag.ContinueOnError)
	global.SetOutput(out)
	transport := global.String("transport", "grpc", "transport: grpc|http")
	address := global.String("address", "", "server address (default localhost:9090 for grpc, http://localhost:8080 for http)")
	tenant := global.String("tenant", "", "tenant_id")
	project := global.String("project", "", "project_id")
	if err := global.Parse(args); err != nil {
		return 2
	}
	rest := global.Args()
	if len(rest) == 0 {
		fmt.Fprintln(out, "usage: mnemovela [--transport grpc|http] [--address ADDR] <command> [flags]")
		fmt.Fprintln(out, "commands: add-episode, add-fact, commit, search, query-facts, list-branches, create-branch, ... , call")
		return 2
	}
	cmd := rest[0]

	addr := *address
	if addr == "" {
		if *transport == "http" {
			addr = "http://localhost:8080"
		} else {
			addr = "localhost:9090"
		}
	}
	var tr mnemovela.Transport
	var err error
	switch *transport {
	case "grpc":
		tr, err = mnemovela.NewGRPCTransport(addr)
	case "http":
		tr = mnemovela.NewJSONRPCTransport(addr)
	default:
		fmt.Fprintf(out, "unknown transport %q (use grpc or http)\n", *transport)
		return 2
	}
	if err != nil {
		fmt.Fprintf(out, "connect: %v\n", err)
		return 1
	}
	client := mnemovela.New(tr)
	defer client.Close()

	params := map[string]any{}
	if *tenant != "" {
		params["tenant_id"] = *tenant
	}
	if *project != "" {
		params["project_id"] = *project
	}

	var method string
	if cmd == "call" {
		// mnemovela call <method> --param k=v --param k2=v2
		fs := flag.NewFlagSet("call", flag.ContinueOnError)
		fs.SetOutput(out)
		var kv multiFlag
		fs.Var(&kv, "param", "k=v (repeatable); values parsed as JSON, else string")
		if err := fs.Parse(rest[1:]); err != nil {
			return 2
		}
		if fs.NArg() < 1 {
			fmt.Fprintln(out, "usage: mnemovela call <mnemovela.method> [--param k=v ...]")
			return 2
		}
		method = fs.Arg(0)
		for _, item := range kv {
			k, v, ok := strings.Cut(item, "=")
			if !ok {
				fmt.Fprintf(out, "bad --param %q (want k=v)\n", item)
				return 2
			}
			var parsed any
			if json.Unmarshal([]byte(v), &parsed) == nil {
				params[k] = parsed
			} else {
				params[k] = v
			}
		}
	} else {
		spec, ok := commands[cmd]
		if !ok {
			fmt.Fprintf(out, "unknown command: %s\n", cmd)
			return 2
		}
		method = spec.rpc
		fs := flag.NewFlagSet(cmd, flag.ContinueOnError)
		fs.SetOutput(out)
		strVals := map[string]*string{}
		intVals := map[string]*int{}
		fltVals := map[string]*float64{}
		boolVals := map[string]*bool{}
		jsonVals := map[string]*string{}
		for _, n := range spec.strs {
			strVals[n] = fs.String(n, "", "")
		}
		for _, n := range spec.ints {
			intVals[n] = fs.Int(n, 0, "")
		}
		for _, n := range spec.flts {
			fltVals[n] = fs.Float64(n, 0, "")
		}
		for _, n := range spec.bools {
			boolVals[n] = fs.Bool(n, false, "")
		}
		for _, n := range spec.jsons {
			jsonVals[n] = fs.String(n, "", "JSON object")
		}
		if err := fs.Parse(rest[1:]); err != nil {
			return 2
		}
		// include only flags the user set
		set := map[string]bool{}
		fs.Visit(func(f *flag.Flag) { set[f.Name] = true })
		for n, p := range strVals {
			if set[n] {
				params[kebabToSnake(n)] = *p
			}
		}
		for n, p := range intVals {
			if set[n] {
				params[kebabToSnake(n)] = *p
			}
		}
		for n, p := range fltVals {
			if set[n] {
				params[kebabToSnake(n)] = *p
			}
		}
		for n, p := range boolVals {
			if set[n] {
				params[kebabToSnake(n)] = *p
			}
		}
		for n, p := range jsonVals {
			if set[n] {
				var obj any
				if err := json.Unmarshal([]byte(*p), &obj); err != nil {
					fmt.Fprintf(out, "--%s must be valid JSON: %v\n", n, err)
					return 2
				}
				params[kebabToSnake(n)] = obj
			}
		}
	}

	raw, err := client.Invoke(context.Background(), method, params)
	if err != nil {
		fmt.Fprintf(out, "error: %v\n", err)
		return 1
	}
	var pretty any
	_ = json.Unmarshal(raw, &pretty)
	enc := json.NewEncoder(out)
	enc.SetIndent("", "  ")
	_ = enc.Encode(pretty)
	return 0
}

type multiFlag []string

func (m *multiFlag) String() string { return strings.Join(*m, ",") }
func (m *multiFlag) Set(v string) error {
	*m = append(*m, v)
	return nil
}

func main() { os.Exit(run(os.Args[1:], os.Stdout)) }
