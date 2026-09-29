import sys
import mlflow

MODEL_NAME = "customer-churn-model"
RUN_ID_FILE = "/tmp/selected_run_id"


def main():
    try:
        with open(RUN_ID_FILE, "r", encoding="utf-8") as file:
            run_id = file.read().strip()
    except FileNotFoundError:
        print(f"Selected run file not found: {RUN_ID_FILE}")
        print("Run select_model.py successfully before registration.")
        sys.exit(1)

    if not run_id:
        print("Selected run ID is empty")
        sys.exit(1)

    model_uri = f"runs:/{run_id}/model"

    print("\nRegistering selected model:")
    print(f"Run ID: {run_id}")
    print(f"Model: {MODEL_NAME}")

    result = mlflow.register_model(
        model_uri=model_uri,
        name=MODEL_NAME,
    )

    print("\nModel successfully registered.")
    print(f"Model: {result.name}")
    print(f"Version: {result.version}")

    with open("/tmp/registered_model_version", "w", encoding="utf-8") as file:
        file.write(str(result.version))


if __name__ == "__main__":
    main()
