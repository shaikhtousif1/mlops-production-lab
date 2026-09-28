import mlflow
import sys


MODEL_NAME = "customer-churn-model"


def main():

    runs = mlflow.search_runs()

    # Only consider the current dataset version
    runs = runs[
        runs["tags.dataset_version"] == "v2"
    ]

    # Only consider runs with the required metrics
    candidates = runs.dropna(
        subset=[
            "metrics.mean_f1",
            "metrics.f1",
            "metrics.recall",
        ]
    )

    if candidates.empty:
        print("No valid model candidates found")
        sys.exit(1)

    # Select the same candidate that passed the quality gate
    selected = candidates.sort_values(
        by=[
            "metrics.mean_f1",
            "metrics.std_f1",
            "metrics.recall",
            "metrics.precision",
        ],
        ascending=[
            False,
            True,
            False,
            False,
        ],
    ).iloc[0]

    run_id = selected["run_id"]

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


if __name__ == "__main__":
    main()
