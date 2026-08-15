from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Mapping


DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PHASES = {
    "idle",
    "precharge",
    "constant_current",
    "constant_voltage",
    "complete",
    "fault",
}
FAULTS = {"none", "invalid_sensor", "over_temperature", "over_voltage"}


class ValidationError(ValueError):
    pass


def _finite_float(payload: Mapping[str, Any], field: str) -> float:
    try:
        value = float(payload[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be numeric") from exc
    if not math.isfinite(value):
        raise ValidationError(f"{field} must be finite")
    return value


def _boolean(payload: Mapping[str, Any], field: str) -> bool:
    value = payload.get(field)
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean")
    return value


@dataclass(frozen=True)
class Telemetry:
    schema_version: int
    device_id: str
    timestamp_ms: int
    voltage_v: float
    current_ma: float
    temperature_c: float
    battery_present: bool
    phase: str
    fault: str
    charge_enabled: bool
    requested_current_ma: float
    delivered_capacity_mah: float
    cycle_count: int

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "Telemetry":
        try:
            schema_version = int(payload["schema_version"])
            timestamp_ms = int(payload["timestamp_ms"])
            device_id = str(payload["device_id"])
            phase = str(payload["phase"])
            fault = str(payload["fault"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError("missing or invalid required field") from exc

        voltage_v = _finite_float(payload, "voltage_v")
        current_ma = _finite_float(payload, "current_ma")
        temperature_c = _finite_float(payload, "temperature_c")
        requested_current_ma = _finite_float(payload, "requested_current_ma")
        delivered_capacity_mah = _finite_float(payload, "delivered_capacity_mah")
        battery_present = _boolean(payload, "battery_present")
        charge_enabled = _boolean(payload, "charge_enabled")
        try:
            cycle_count = int(payload["cycle_count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError("cycle_count must be an integer") from exc

        if schema_version != 1:
            raise ValidationError("unsupported schema_version")
        if not DEVICE_ID_PATTERN.fullmatch(device_id):
            raise ValidationError("device_id contains unsupported characters")
        if timestamp_ms < 0:
            raise ValidationError("timestamp_ms must be non-negative")
        if not 0.0 <= voltage_v <= 6.0:
            raise ValidationError("voltage_v outside expected single-cell range")
        if not -100.0 <= current_ma <= 5_000.0:
            raise ValidationError("current_ma outside sensor range")
        if not -20.0 <= temperature_c <= 100.0:
            raise ValidationError("temperature_c outside sensor range")
        if not 0.0 <= requested_current_ma <= 5_000.0:
            raise ValidationError("requested_current_ma outside supported range")
        if not 0.0 <= delivered_capacity_mah <= 100_000.0:
            raise ValidationError("delivered_capacity_mah outside supported range")
        if not 0 <= cycle_count <= 100_000:
            raise ValidationError("cycle_count outside supported range")
        if phase not in PHASES:
            raise ValidationError("unknown charge phase")
        if fault not in FAULTS:
            raise ValidationError("unknown fault")

        return cls(
            schema_version=schema_version,
            device_id=device_id,
            timestamp_ms=timestamp_ms,
            voltage_v=voltage_v,
            current_ma=current_ma,
            temperature_c=temperature_c,
            battery_present=battery_present,
            phase=phase,
            fault=fault,
            charge_enabled=charge_enabled,
            requested_current_ma=requested_current_ma,
            delivered_capacity_mah=delivered_capacity_mah,
            cycle_count=cycle_count,
        )

    def to_dynamodb_item(self) -> dict[str, Any]:
        item = asdict(self)
        for field in (
            "voltage_v",
            "current_ma",
            "temperature_c",
            "requested_current_ma",
            "delivered_capacity_mah",
        ):
            item[field] = Decimal(str(item[field]))
        item["power_w"] = Decimal(str(self.voltage_v * self.current_ma / 1_000.0))
        return item

    def model_features(self) -> list[float]:
        phase_order = {
            "idle": 0.0,
            "precharge": 1.0,
            "constant_current": 2.0,
            "constant_voltage": 3.0,
            "complete": 4.0,
            "fault": 5.0,
        }
        return [
            self.voltage_v,
            self.current_ma,
            self.temperature_c,
            self.voltage_v * self.current_ma / 1_000.0,
            phase_order[self.phase],
            self.delivered_capacity_mah,
            float(self.cycle_count),
        ]
