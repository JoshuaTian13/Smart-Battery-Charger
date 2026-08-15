import json
import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inference import input_fn, output_fn, predict_fn  # noqa: E402


class FakeModel:
    def predict(self, rows):
        if len(rows) != 1 or len(rows[0]) != 7:
            raise AssertionError("unexpected feature shape")
        return [101.5]


class InferenceTests(unittest.TestCase):
    def test_json_contract_and_bounded_prediction(self):
        features = input_fn(
            json.dumps({"features": [4.0, 500.0, 30.0, 2.0, 2.0, 700.0, 42.0]}),
            "application/json; charset=utf-8",
        )
        prediction = predict_fn(features, {"model": FakeModel()})
        body, content_type = output_fn(prediction, "*/*")
        self.assertEqual(json.loads(body), {"health_pct": 100.0})
        self.assertEqual(content_type, "application/json")

    def test_non_finite_feature_is_rejected(self):
        with self.assertRaises(ValueError):
            input_fn(
                json.dumps({"features": [4.0, 500.0, math.nan, 2.0, 2.0, 700.0, 42.0]}),
                "application/json",
            )


if __name__ == "__main__":
    unittest.main()
