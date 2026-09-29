import sys
import mlflow
from mlflow import MlflowClient

MODEL_NAME = "customer-churn-model"
VERSION_FILE = "/tmp/registered_model_version"


def main():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as file:
            version = file.read().strip()
    except FileNotFoundError:
        print(f"Registered model version file not found: {VERSION_FILE}")
        print("Run register_model.py successfully before promotion.")
        sys.exit(1)

    if not version:
        print("Registered model version is empty")
        sys.exit(1)

    client = MlflowClient()

    print("\nPromoting model to production:")
    print(f"Model: {MODEL_NAME}")
    print(f"Version: {version}")

    client.set_registered_model_alias(
        name=MODEL_NAME,
        alias="production",
        version=version,
    )

    production_version = client.get_model_version_by_alias(
        MODEL_NAME,
        "production",
    )

    print("\nProduction model:")
    print(f"Model: {production_version.name}")
    print(f"Version: {production_version.version}")
    print(f"Run ID: {production_version.run_id}")
    print("\nModel successfully promoted to production.")


if __name__ == "__main__":
    main()
