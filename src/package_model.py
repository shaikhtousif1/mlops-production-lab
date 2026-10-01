import json
import os
import sys

import joblib
import mlflow
from huggingface_hub import HfApi
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
    dataset_version = run.data.tags.get("dataset_version")
    metadata = {
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "run_id": run_id,
        "dataset_version": dataset_version,
    }

    with open(MODEL_METADATA_OUTPUT, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
        file.write("\n")

    print(f"Packaged model written to: {MODEL_OUTPUT}")
    print(f"Model metadata written to: {MODEL_METADATA_OUTPUT}")

    # Publish the immutable packaged artifact to Hugging Face.
    # The API image still contains the model, so the artifact store is not a
    # runtime dependency; it gives us a production-style artifact lifecycle.
    hf_repo_id = os.environ.get("HF_REPO_ID")
    hf_token = os.environ.get("HF_TOKEN")

    if not hf_repo_id or not hf_token:
        print("HF_REPO_ID and HF_TOKEN are required to publish the model artifact.")
        sys.exit(1)

    hf_api = HfApi(token=hf_token)
    artifact_prefix = f"versions/{model_version}"

    print("\nPublishing model artifact to Hugging Face:")
    print(f"Repository: {hf_repo_id}")
    print(f"Path: {artifact_prefix}/")

    hf_api.upload_file(
        path_or_fileobj=MODEL_OUTPUT,
        path_in_repo=f"{artifact_prefix}/{MODEL_OUTPUT}",
        repo_id=hf_repo_id,
        repo_type="model",
        commit_message=f"Publish customer churn model v{model_version}",
    )

    hf_api.upload_file(
        path_or_fileobj=MODEL_METADATA_OUTPUT,
        path_in_repo=f"{artifact_prefix}/{MODEL_METADATA_OUTPUT}",
        repo_id=hf_repo_id,
        repo_type="model",
        commit_message=f"Publish metadata for customer churn model v{model_version}",
    )

    print("Model artifact successfully published to Hugging Face.")


if __name__ == "__main__":
    main()
