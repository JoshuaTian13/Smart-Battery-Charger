# AWS infrastructure

The SAM/CloudFormation template creates:

- a mutually authenticated AWS IoT Core ingestion path;
- a Lambda telemetry processor;
- an encrypted, point-in-time-recoverable DynamoDB time-series table;
- an encrypted S3 bucket for model artifacts;
- optional SageMaker endpoint invocation;
- a read-only HTTP API for the dashboard; and
- least-scope device publishing through the example IoT policy.

## Deploy

```bash
sam build --template-file infrastructure/template.yaml
sam deploy --guided
```

Validate the template before deploying:

```bash
pip install -r infrastructure/requirements-dev.txt
cfn-lint infrastructure/template.yaml
```

The first deployment can leave `SageMakerEndpointName` empty. After training and deploying a model, update the stack with its endpoint name to enable inference.

Replace `REGION` and `ACCOUNT_ID` in `iot-policy.json` before attaching the policy to an AWS IoT thing certificate.
