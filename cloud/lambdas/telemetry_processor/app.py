from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable


SHARED_DIR = Path(__file__).resolve().parents[2] / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from telemetry import Telemetry, ValidationError  # noqa: E402


def _decode_event(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        return event
    if isinstance(body, str):
        return json.loads(body)
    if isinstance(body, dict):
        return body
    raise ValidationError("event body must be an object or JSON string")


def sagemaker_predictor(runtime_client: Any, endpoint_name: str) -> Callable[[list[float]], float]:
    def predict(features: list[float]) -> float:
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps({"features": features}).encode("utf-8"),
        )
        result = json.loads(response["Body"].read().decode("utf-8"))
        return float(result["health_pct"])

    return predict


def process_event(
    event: dict[str, Any],
    *,
    table: Any,
    predictor: Callable[[list[float]], float] | None = None,
) -> dict[str, Any]:
    telemetry = Telemetry.from_payload(_decode_event(event))
    item = telemetry.to_dynamodb_item()
    if predictor is not None and telemetry.fault == "none":
        prediction = max(0.0, min(100.0, predictor(telemetry.model_features())))
        item["predicted_health_pct"] = Decimal(str(round(prediction, 3)))

    table.put_item(
        Item=item,
        ConditionExpression=(
            "attribute_not_exists(device_id) AND "
            "attribute_not_exists(timestamp_ms)"
        ),
    )
    return item


def _is_duplicate_write(error: Exception) -> bool:
    response = getattr(error, "response", {})
    return (
        isinstance(response, dict)
        and response.get("Error", {}).get("Code")
        == "ConditionalCheckFailedException"
    )


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    try:
        import boto3

        table = boto3.resource("dynamodb").Table(os.environ["TELEMETRY_TABLE_NAME"])
        endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME", "").strip()
        predictor = None
        if endpoint_name:
            predictor = sagemaker_predictor(
                boto3.client("sagemaker-runtime"),
                endpoint_name,
            )
        item = process_event(event, table=table, predictor=predictor)
        return {
            "statusCode": 202,
            "body": json.dumps(
                {
                    "accepted": True,
                    "device_id": item["device_id"],
                    "timestamp_ms": item["timestamp_ms"],
                }
            ),
        }
    except (ValidationError, json.JSONDecodeError) as exc:
        return {
            "statusCode": 400,
            "body": json.dumps({"accepted": False, "error": str(exc)}),
        }
    except Exception as exc:
        if _is_duplicate_write(exc):
            return {
                "statusCode": 200,
                "body": json.dumps({"accepted": True, "duplicate": True}),
            }
        raise
