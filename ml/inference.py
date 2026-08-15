from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import joblib


def model_fn(model_dir: str) -> dict[str, Any]:
    return joblib.load(Path(model_dir) / "model.joblib")


def input_fn(request_body: str, content_type: str) -> list[float]:
    if content_type.split(";", 1)[0].strip() != "application/json":
        raise ValueError(f"unsupported content type: {content_type}")
    payload = json.loads(request_body)
    features = [float(value) for value in payload["features"]]
    if len(features) != 7:
        raise ValueError("expected seven ordered charger features")
    if not all(math.isfinite(value) for value in features):
        raise ValueError("charger features must be finite")
    return features


def predict_fn(features: list[float], bundle: dict[str, Any]) -> float:
    prediction = float(bundle["model"].predict([features])[0])
    return max(0.0, min(100.0, prediction))


def output_fn(prediction: float, accept: str) -> tuple[str, str]:
    if accept not in {"application/json", "*/*"}:
        raise ValueError(f"unsupported accept type: {accept}")
    return json.dumps({"health_pct": round(prediction, 3)}), "application/json"
