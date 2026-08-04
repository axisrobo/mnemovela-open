import http from "node:http";
import type { AddressInfo } from "node:net";

export async function startFakeServer(): Promise<{ url: string; close: () => Promise<void> }> {
  const server = http.createServer((req, res) => {
    let raw = "";
    req.on("data", (c) => (raw += c));
    req.on("end", () => {
      const body = JSON.parse(raw || "{}");
      const id = body.id ?? null;
      const method: string = body.method ?? "";
      let result: unknown;
      let error: { code: number; message: string } | undefined;
      if (method === "mnemovela.add_episode") {
        result = { commit_id: "mem_1", branch_name: body.params?.branch_name, memory_type: "episode" };
      } else if (method === "mnemovela.search_memory") {
        result = [{ commit: { commit_id: "mem_1" }, score: 0.9 }, { commit: { commit_id: "mem_2" }, score: 0.5 }];
      } else if (method === "mnemovela.list_branches") {
        result = [{ branch_name: "main", head_sequence: 3 }];
      } else {
        error = { code: -32601, message: `method not found: ${method}` };
      }
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify(error ? { jsonrpc: "2.0", id, error } : { jsonrpc: "2.0", id, result }));
    });
  });
  await new Promise<void>((r) => server.listen(0, r));
  const { port } = server.address() as AddressInfo;
  return {
    url: `http://localhost:${port}`,
    close: () => new Promise<void>((r) => server.close(() => r())),
  };
}
