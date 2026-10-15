import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mnemovela_client import MnemovelaClient

ADDR = os.getenv("MNEMOVELA_GRPC_ADDR")


@unittest.skipUnless(ADDR, "set MNEMOVELA_GRPC_ADDR to run live integration test")
class TestLiveServer(unittest.TestCase):
    def test_add_and_search(self):
        with MnemovelaClient(ADDR) as c:
            c.add_episode(branch_name="main", content="integration probe")
            results = c.search_memory("main", "integration", top_k=5)
            self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
