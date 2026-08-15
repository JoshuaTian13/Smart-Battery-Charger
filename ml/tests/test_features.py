import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cloud" / "shared"))

from features import FEATURE_NAMES, row_to_features  # noqa: E402
from telemetry import Telemetry  # noqa: E402


class FeatureTests(unittest.TestCase):
    def test_feature_contract_matches_cloud_order(self):
        row = {
            "schema_version": 1,
            "device_id": "charger-001",
            "timestamp_ms": 1_700_000_000_000,
            "voltage_v": 4.0,
            "current_ma": 500.0,
            "temperature_c": 30.0,
            "battery_present": True,
            "phase": "constant_current",
            "fault": "none",
            "charge_enabled": True,
            "requested_current_ma": 800.0,
            "delivered_capacity_mah": 700.0,
            "cycle_count": 42,
        }
        features = row_to_features(row)
        self.assertEqual(len(features), len(FEATURE_NAMES))
        self.assertEqual(features, [4.0, 500.0, 30.0, 2.0, 2.0, 700.0, 42.0])
        self.assertEqual(features, Telemetry.from_payload(row).model_features())

    def test_unknown_phase_is_rejected(self):
        with self.assertRaises(KeyError):
            row_to_features(
                {
                    "voltage_v": 4.0,
                    "current_ma": 500.0,
                    "temperature_c": 30.0,
                    "phase": "mystery",
                    "delivered_capacity_mah": 700.0,
                    "cycle_count": 42,
                }
            )


if __name__ == "__main__":
    unittest.main()
