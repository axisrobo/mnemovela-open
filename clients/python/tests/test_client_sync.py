import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mnemovela_client import MnemovelaClient
from fake_server import serve


class TestSyncClient(unittest.TestCase):
    def test_add_episode(self):
        with serve() as addr:
            with MnemovelaClient(addr) as c:
                commit = c.add_episode(branch_name="main", content="hello")
                self.assertEqual(commit["commit_id"], "mem_1")
                self.assertEqual(commit["branch_name"], "main")
                self.assertEqual(commit["payload"]["content"], "hello")

    def test_commit_memory_roundtrips_payload(self):
        with serve() as addr:
            with MnemovelaClient(addr) as c:
                commit = c.commit_memory(branch_name="main", memory_type="knowledge",
                                         payload={"summary": "s", "score": 1.0})
                self.assertEqual(commit["payload"]["summary"], "s")
                self.assertEqual(commit["payload"]["score"], 1.0)

    def test_search_memory(self):
        with serve() as addr:
            with MnemovelaClient(addr) as c:
                results = c.search_memory("main", "hello", top_k=5)
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0]["commit"]["commit_id"], "mem_1")
                self.assertAlmostEqual(results[0]["score"], 0.9)

    def test_list_branches(self):
        with serve() as addr:
            with MnemovelaClient(addr) as c:
                branches = c.list_branches()
                self.assertEqual(branches[0]["branch_name"], "main")


if __name__ == "__main__":
    unittest.main()
