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
RELEASES_PREFIX = "releases"


def get_next_release_version(hf_api, repo_id):
    """Return the next persistent release number stored in Hugging Face."""
    versions = []

    try:
        entries = hf_api.list_repo_tree(
            repo_id=repo_id,
            path=RELEASES_PREFIX,
            recursive=False,
            repo_type="model",
        )

        for entry in entries:
            path = getattr(entry, "path", "")
            if not path.startswith(f"{RELEASES_PREFIX}/"):
                continue

            name = path.rsplit("/", 1)[-1]
            if name.isdigit():
                versions.append(int(name))
    except Exception as exc:
        print(f"No existing release directory found; starting at release 1 ({exc}).")

    return max(versions, default=0) + 1


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

    mlflow_model_version = str(production_version.version)
    run_id = production_version.run_id
    model_uri = f"models:/{MODEL_NAME}@production"

    hf_repo_id = os.environ.get("HF_REPO_ID")
    hf_token = os.environ.get("HF_TOKEN")

    if not hf_repo_id or not hf_token:
        print("HF_REPO_ID and HF_TOKEN are required to publish the model artifact.")
        sys.exit(1)

    hf_api = HfApi(token=hf_token)
    release_version = get_next_release_version(hf_api, hf_repo_id)

    print("\nPackaging production model:")
    print(f"Model: {MODEL_NAME}")
    print(f"Model release version: {release_version}")
    print(f"MLflow version (CI-local): {mlflow_model_version}")
    print(f"Run ID: {run_id}")
    print(f"Model URI: {model_uri}")

    model = mlflow.sklearn.load_model(model_uri)
    joblib.dump(model, MODEL_OUTPUT)

    run = client.get_run(run_id)
    dataset_version = run.data.tags.get("dataset_version")
    metadata = {
        "model_name": MODEL_NAME,
        "model_release_version": str(release_version),
        "mlflow_model_version": mlflow_model_version,
        "run_id": run_id,
        "dataset_version": dataset_version,
    }

    with open(MODEL_METADATA_OUTPUT, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
        file.write("\n")

    print(f"Packaged model written to: {MODEL_OUTPUT}")
    print(f"Model metadata written to: {MODEL_METADATA_OUTPUT}")

    artifact_prefix = f"{RELEASES_PREFIX}/{release_version}"

    print("\nPublishing promoted model artifact to Hugging Face:")
    print(f"Repository: {hf_repo_id}")
    print(f"Release path: {artifact_prefix}/")

    hf_api.upload_file(
        path_or_fileobj=MODEL_OUTPUT,
        path_in_repo=f"{artifact_prefix}/{MODEL_OUTPUT}",
        repo_id=hf_repo_id,
        repo_type="model",
        commit_message=f"Publish customer churn release v{release_version}",
    )

    hf_api.upload_file(
        path_or_fileobj=MODEL_METADATA_OUTPUT,
        path_in_repo=f"{artifact_prefix}/{MODEL_METADATA_OUTPUT}",
        repo_id=hf_repo_id,
        repo_type="model",
        commit_message=f"Publish metadata for customer churn release v{release_version}",
    )

    print("Model release successfully published to Hugging Face.")


if __name__ == "__main__":
    main()
