from __future__ import annotations

import argparse
import tarfile
from pathlib import Path

import sagemaker
from sagemaker.sklearn.model import SKLearnModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy the trained advisory model to SageMaker")
    parser.add_argument("--role-arn", required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--model-dir", type=Path, default=Path("ml/artifacts"))
    parser.add_argument("--endpoint-name", default="battery-health-advisory")
    args = parser.parse_args()

    artifact = args.model_dir / "model.tar.gz"
    with tarfile.open(artifact, "w:gz") as archive:
        archive.add(args.model_dir / "model.joblib", arcname="model.joblib")

    session = sagemaker.Session(
        boto_session=__import__("boto3").Session(region_name=args.region)
    )
    model_data = session.upload_data(
        str(artifact),
        bucket=args.bucket,
        key_prefix="smart-battery-charger/models",
    )
    model = SKLearnModel(
        model_data=model_data,
        role=args.role_arn,
        entry_point="inference.py",
        source_dir=str(Path(__file__).resolve().parent),
        framework_version="1.4-2",
        py_version="py3",
        sagemaker_session=session,
    )
    model.deploy(
        initial_instance_count=1,
        instance_type="ml.m5.large",
        endpoint_name=args.endpoint_name,
    )
    print(args.endpoint_name)


if __name__ == "__main__":
    main()
