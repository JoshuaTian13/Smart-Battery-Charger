import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUERY_PATH = ROOT / "cloud" / "lambdas" / "query_api" / "app.py"
spec = importlib.util.spec_from_file_location("query_api", QUERY_PATH)
query_api = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["query_api"] = query_api
spec.loader.exec_module(query_api)


class FakeTable:
    def __init__(self):
        self.kwargs = None

    def query(self, **kwargs):
        self.kwargs = kwargs
        return {"Items": [{"device_id": "charger-001", "timestamp_ms": 5}]}


class QueryApiTests(unittest.TestCase):
    def test_queries_latest_items_with_bounded_limit(self):
        table = FakeTable()
        items = query_api.query_device(table, "charger-001", 5_000)
        self.assertEqual(len(items), 1)
        self.assertEqual(table.kwargs["Limit"], 500)
        self.assertFalse(table.kwargs["ScanIndexForward"])


if __name__ == "__main__":
    unittest.main()
