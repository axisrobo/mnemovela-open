import { test } from "node:test";
import assert from "node:assert/strict";
import { MnemeClient } from "../src/client.js";
import { MnemeError } from "../src/errors.js";
import { startFakeServer } from "./fake_server.js";

test("addEpisode returns a commit", async () => {
  const s = await startFakeServer();
  try {
    const c = new MnemeClient(s.url);
    const commit = await c.addEpisode({ branch_name: "main", content: "hi" }) as any;
    assert.equal(commit.commit_id, "mem_1");
    assert.equal(commit.branch_name, "main");
  } finally {
    await s.close();
  }
});

test("searchMemory returns results", async () => {
  const s = await startFakeServer();
  try {
    const c = new MnemeClient(s.url);
    const results = await c.searchMemory({ branch_name: "main", query: "hi", top_k: 5 }) as any[];
    assert.equal(results.length, 2);
  } finally {
    await s.close();
  }
});

test("unknown method throws MnemeError -32601", async () => {
  const s = await startFakeServer();
  try {
    const c = new MnemeClient(s.url);
    await assert.rejects(() => c.request("mnemovela.nope"), (e: unknown) => e instanceof MnemeError && (e as MnemeError).code === -32601);
  } finally {
    await s.close();
  }
});
