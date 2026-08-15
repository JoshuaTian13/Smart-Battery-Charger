from __future__ import annotations

import math
from typing import Mapping


FEATURE_NAMES = [
    "voltage_v",
    "current_ma",
    "temperature_c",
    "power_w",
    "phase_code",
    "delivered_capacity_mah",
    "cycle_count",
]

PHASE_CODES = {
    "idle": 0.0,
    "precharge": 1.0,
    "constant_current": 2.0,
    "constant_voltage": 3.0,
    "complete": 4.0,
    "fault": 5.0,
}


def row_to_features(row: Mapping[str, object]) -> list[float]:
    voltage = float(row["voltage_v"])
    current = float(row["current_ma"])
    temperature = float(row["temperature_c"])
    phase = str(row["phase"])
    values = [
        voltage,
        current,
        temperature,
        voltage * current / 1_000.0,
        PHASE_CODES[phase],
        float(row["delivered_capacity_mah"]),
        float(row["cycle_count"]),
    ]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("model features must be finite")
    return values
