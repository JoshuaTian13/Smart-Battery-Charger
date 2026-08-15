import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROCESSOR_PATH = ROOT / "cloud" / "lambdas" / "telemetry_processor" / "app.py"
spec = importlib.util.spec_from_file_location("telemetry_processor", PROCESSOR_PATH)
processor = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["telemetry_processor"] = processor
spec.loader.exec_module(processor)


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, **kwargs):
        self.items.append(kwargs)
        return {}


def valid_event():
    return {
        "schema_version": 1,
        "device_id": "charger-001",
        "timestamp_ms": 123_456,
        "voltage_v": 4.02,
        "current_ma": 420.0,
        "temperature_c": 31.5,
        "battery_present": True,
        "phase": "constant_current",
        "fault": "none",
        "charge_enabled": True,
        "requested_current_ma": 800.0,
        "delivered_capacity_mah": 612.4,
        "cycle_count": 83,
    }


class TelemetryProcessorTests(unittest.TestCase):
    def test_stores_valid_event_and_prediction(self):
        table = FakeTable()
        item = processor.process_event(
            valid_event(),
            table=table,
            predictor=lambda features: 93.25 if len(features) == 7 else 0.0,
        )
        self.assertEqual(item["device_id"], "charger-001")
        self.assertEqual(float(item["power_w"]), 1.6884)
        self.assertEqual(float(item["predicted_health_pct"]), 93.25)
        self.assertIn("attribute_not_exists", table.items[0]["ConditionExpression"])

    def test_rejects_out_of_range_voltage(self):
        event = valid_event()
        event["voltage_v"] = 9.0
        with self.assertRaises(processor.ValidationError):
            processor.process_event(event, table=FakeTable())

    def test_faulted_sample_skips_model(self):
        event = valid_event()
        event["phase"] = "fault"
        event["fault"] = "over_temperature"
        item = processor.process_event(
            event,
            table=FakeTable(),
            predictor=lambda _features: self.fail("predictor should not run"),
        )
        self.assertNotIn("predicted_health_pct", item)

    def test_rejects_string_that_only_looks_boolean(self):
        event = valid_event()
        event["charge_enabled"] = "false"
        with self.assertRaises(processor.ValidationError):
            processor.process_event(event, table=FakeTable())

    def test_detects_dynamodb_conditional_duplicate(self):
        error = RuntimeError("conditional write failed")
        error.response = {
            "Error": {"Code": "ConditionalCheckFailedException"}
        }
        self.assertTrue(processor._is_duplicate_write(error))


if __name__ == "__main__":
    unittest.main()
