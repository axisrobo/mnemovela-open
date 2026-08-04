import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# reuse the mnemovela-client package + its fake gRPC server
_ROOT = Path(__file__).resolve().parents[2]  # clients/
sys.path.insert(0, str(_ROOT / "python" / "src"))
sys.path.insert(0, str(_ROOT / "python" / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fake_server import serve  # from clients/python/tests
from fake_http_server import serve_http  # from clients/python/tests
from mnemovela_cli.main import main


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(argv)
    return rc, buf.getvalue()


class TestCli(unittest.TestCase):
    def test_add_episode_prints_json(self):
        with serve() as addr:
            rc, out = _run(["--address", addr, "add-episode", "--branch", "main", "--content", "hello"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(data["commit_id"], "mem_1")
            self.assertEqual(data["branch_name"], "main")

    def test_search_prints_results(self):
        with serve() as addr:
            rc, out = _run(["--address", addr, "search", "--branch", "main", "--query", "hi", "--top-k", "5"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(len(data), 2)

    def test_list_branches(self):
        with serve() as addr:
            rc, out = _run(["--address", addr, "list-branches"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(data[0]["branch_name"], "main")

    def test_unknown_command_errors(self):
        with self.assertRaises(SystemExit):
            main(["bogus-command"])


class TestCliHttp(unittest.TestCase):
    def test_http_add_episode(self):
        with serve_http() as addr:
            rc, out = _run(["--transport", "http", "--address", addr, "add-episode", "--branch", "main", "--content", "hi"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(data["commit_id"], "mem_1")
            self.assertEqual(data["branch_name"], "main")

    def test_http_search(self):
        with serve_http() as addr:
            rc, out = _run(["--transport", "http", "--address", addr, "search", "--branch", "main", "--query", "x"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(len(data), 2)

    def test_http_list_branches(self):
        with serve_http() as addr:
            rc, out = _run(["--transport", "http", "--address", addr, "list-branches"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(data[0]["branch_name"], "main")

    def test_call_subcommand(self):
        with serve_http() as addr:
            rc, out = _run(["--transport", "http", "--address", addr, "call", "mnemovela.add_episode",
                            "--param", "branch_name=main", "--param", "content=via call"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(data["branch_name"], "main")

    def test_call_unknown_method_error(self):
        with serve_http() as addr:
            rc, out = _run(["--transport", "http", "--address", addr, "call", "mnemovela.nope"])
            self.assertNotEqual(rc, 0)  # MnemeError -> non-zero

    def test_http_identity_params(self):
        with serve_http() as addr:
            rc, out = _run(["--transport", "http", "--address", addr, "--tenant", "t1", "--project", "p1",
                            "add-episode", "--branch", "main", "--content", "x"])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
