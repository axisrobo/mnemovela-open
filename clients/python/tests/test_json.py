import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mnemovela_client._json import to_value, from_value, to_value_map, from_value_map


class TestValueConverters(unittest.TestCase):
    def test_roundtrip_scalars(self):
        for obj in ["hi", 3.5, True, False]:
            self.assertEqual(from_value(to_value(obj)), obj)

    def test_roundtrip_nested(self):
        obj = {"a": "x", "n": 2.0, "b": True, "list": [1.0, "y"], "obj": {"k": "v"}}
        self.assertEqual(from_value(to_value(obj)), obj)

    def test_value_map_roundtrip(self):
        d = {"summary": "s", "score": 1.0, "flag": True}
        self.assertEqual(from_value_map(to_value_map(d)), d)


if __name__ == "__main__":
    unittest.main()
