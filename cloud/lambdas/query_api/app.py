from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any


def _json_default(value: object):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def query_device(table: Any, device_id: str, limit: int) -> list[dict[str, Any]]:
    response = table.query(
        KeyConditionExpression="device_id = :device_id",
        ExpressionAttributeValues={":device_id": device_id},
        ScanIndexForward=False,
        Limit=max(1, min(limit, 500)),
    )
    return list(response.get("Items", []))


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    import boto3

    device_id = str(event.get("pathParameters", {}).get("device_id", "")).strip()
    if not device_id:
        return {"statusCode": 400, "body": json.dumps({"error": "missing device_id"})}
    try:
        limit = int(event.get("queryStringParameters", {}).get("limit", "100"))
    except (TypeError, ValueError):
        return {"statusCode": 400, "body": json.dumps({"error": "limit must be an integer"})}

    table = boto3.resource("dynamodb").Table(os.environ["TELEMETRY_TABLE_NAME"])
    items = query_device(table, device_id, limit)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": os.getenv("ALLOWED_ORIGIN", "*"),
        },
        "body": json.dumps({"device_id": device_id, "items": items}, default=_json_default),
    }
