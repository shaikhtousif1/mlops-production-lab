import json
import sys

import joblib
import mlflow
from mlflow import MlflowClient

MODEL_NAME = "customer-churn-model"
MODEL_OUTPUT = "model.pkl"
MODEL_METADATA_OUTPUT = "model_metadata.json"


def main():
    client = MlflowClient()

    try:
        production_version = client.get_model_version_by_alias(
            MODEL_NAME,
            "production",
        )
    except Exception as exc:
        print(f"Unable to resolve production model: {exc}")
        sys.exit(1)

    model_version = str(production_version.version)
    run_id = production_version.run_id
    model_uri = f"models:/{MODEL_NAME}@production"

    print("\nPackaging production model:")
    print(f"Model: {MODEL_NAME}")
    print(f"Version: {model_version}")
    print(f"Run ID: {run_id}")
    print(f"Model URI: {model_uri}")

    # Load the exact model currently pointed to by the MLflow production alias.
    model = mlflow.sklearn.load_model(model_uri)
    joblib.dump(model, MODEL_OUTPUT)

    # Keep immutable lineage metadata alongside the packaged model.
    run = client.get_run(run_id)
    metadata = {
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "run_id": run_id,
        "dataset_version": run.data.tags.get("dataset_version"),
    }

    with open(MODEL_METADATA_OUTPUT, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
        file.write("\n")

    print(f"Packaged model written to: {MODEL_OUTPUT}")
    print(f"Model metadata written to: {MODEL_METADATA_OUTPUT}")


if __name__ == "__main__":
    main()
