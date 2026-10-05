"""Deliberately roll the production alias back to a known MLflow model version."""

import argparse
from mlflow import MlflowClient

MODEL_NAME = "customer-churn-model"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="Known-good MLflow model version.")
    args = parser.parse_args()

    client = MlflowClient()
    target = client.get_model_version(MODEL_NAME, args.version)

    print(f"Rolling {MODEL_NAME} production alias back to version {target.version}")
    print(f"Run ID: {target.run_id}")

    client.set_registered_model_alias(
        name=MODEL_NAME,
        alias="production",
        version=target.version,
    )

    current = client.get_model_version_by_alias(MODEL_NAME, "production")
    print(f"Production alias now points to version {current.version}")
    print(f"Run ID: {current.run_id}")


if __name__ == "__main__":
    main()
