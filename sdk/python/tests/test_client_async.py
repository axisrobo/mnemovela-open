import asyncio, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mnemovela_client import AsyncMnemovelaClient
from fake_server import serve


class TestAsyncClient(unittest.TestCase):
    def test_add_episode_async(self):
        async def run():
            with serve() as addr:
                client = AsyncMnemovelaClient(addr)
                commit = await client.add_episode(branch_name="main", content="hi")
                await client.close()
                return commit
        commit = asyncio.run(run())
        self.assertEqual(commit["commit_id"], "mem_1")

    def test_search_async(self):
        async def run():
            with serve() as addr:
                client = AsyncMnemovelaClient(addr)
                results = await client.search_memory("main", "hi", top_k=3)
                await client.close()
                return results
        results = asyncio.run(run())
        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
