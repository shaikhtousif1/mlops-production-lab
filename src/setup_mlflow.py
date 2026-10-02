import os
import sys

import boto3
import mlflow
from botocore.exceptions import ClientError
from mlflow import MlflowClient


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}")
        sys.exit(1)
    return value


def main() -> None:
    tracking_uri = required("MLFLOW_TRACKING_URI")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "customer-churn-ci")
    bucket = required("SUPABASE_STORAGE_BUCKET")
    endpoint = required("MLFLOW_S3_ENDPOINT_URL")
    region = required("AWS_DEFAULT_REGION")
    artifact_location = f"s3://{bucket}/mlflow-artifacts"

    mlflow.set_tracking_uri(tracking_uri)

    # Supabase Storage exposes an S3-compatible API. Create the bucket once if
    # it does not already exist, so CI remains self-contained after secrets are set.
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=required("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=required("AWS_SECRET_ACCESS_KEY"),
    )

    try:
        s3.head_bucket(Bucket=bucket)
        print(f"Storage bucket already exists: {bucket}")
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in {"404", "NoSuchBucket", "NotFound"}:
            print(f"Creating Supabase Storage bucket: {bucket}")
            s3.create_bucket(Bucket=bucket)
        else:
            raise

    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(experiment_name)

    if experiment is None:
        experiment_id = client.create_experiment(
            experiment_name,
            artifact_location=artifact_location,
        )
        print(f"Created MLflow experiment: {experiment_name}")
        print(f"Experiment ID: {experiment_id}")
        print(f"Artifact location: {artifact_location}")
    else:
        print(f"MLflow experiment already exists: {experiment_name}")
        print(f"Experiment ID: {experiment.experiment_id}")
        print(f"Artifact location: {experiment.artifact_location}")

        if experiment.artifact_location != artifact_location:
            print("ERROR: Existing experiment has an unexpected artifact location.")
            print(f"Expected: {artifact_location}")
            print(f"Actual:   {experiment.artifact_location}")
            sys.exit(1)


if __name__ == "__main__":
    main()
