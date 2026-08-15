# AWS services

## Telemetry processor

The IoT rule invokes `cloud/lambdas/telemetry_processor/app.py` for each device message. The handler:

1. validates schema, identity, addressable ranges, phase, and fault fields;
2. derives instantaneous power;
3. optionally invokes a SageMaker endpoint for an advisory health estimate;
4. stores the measurement in DynamoDB with an idempotent device/timestamp key; and
5. skips model inference when the embedded controller reports a fault.

## Query API

`cloud/lambdas/query_api/app.py` reads newest-first device history from DynamoDB through an HTTP API used by the React dashboard. Limits are bounded to prevent unbounded reads.

## Local verification

The cloud tests use in-memory fake AWS clients, so validation, model gating, idempotent write configuration, and query behavior can be checked without credentials:

```bash
python3 -m unittest discover -s cloud/tests
```
