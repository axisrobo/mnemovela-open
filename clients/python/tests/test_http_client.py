import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_http_server import serve_http
from mnemovela_client import MnemeHttpClient, AsyncMnemeHttpClient, MnemeError


class TestHttpClient(unittest.TestCase):
    def test_add_episode(self):
        with serve_http() as url:
            c = MnemeHttpClient(url)
            commit = c.add_episode(branch_name="main", content="hi")
            self.assertEqual(commit["commit_id"], "mem_1")
            self.assertEqual(commit["branch_name"], "main")

    def test_search(self):
        with serve_http() as url:
            c = MnemeHttpClient(url)
            results = c.search_memory(branch_name="main", query="hi", top_k=5)
            self.assertEqual(len(results), 2)

    def test_unknown_method_raises(self):
        with serve_http() as url:
            c = MnemeHttpClient(url)
            with self.assertRaises(MnemeError) as ctx:
                c.call("mnemovela.nope")
            self.assertEqual(ctx.exception.code, -32601)

    def test_async_add_episode(self):
        async def run():
            with serve_http() as url:
                c = AsyncMnemeHttpClient(url)
                return await c.add_episode(branch_name="main", content="hi")
        commit = asyncio.run(run())
        self.assertEqual(commit["commit_id"], "mem_1")


if __name__ == "__main__":
    unittest.main()
