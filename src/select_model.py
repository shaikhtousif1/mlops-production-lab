import os
import sys
import mlflow

MIN_CV_F1 = 0.60
MIN_TEST_F1 = 0.60
MIN_RECALL = 0.60
OUTPUT_FILE = "/tmp/selected_run_id"


def main():
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "customer-churn-ci")
    experiment = mlflow.get_experiment_by_name(experiment_name)

    if experiment is None:
        print(f"MLflow experiment not found: {experiment_name}")
        sys.exit(1)

    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

    # Only consider the current dataset version
    runs = runs[runs["tags.dataset_version"] == "v2"]

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

    selected = candidates.sort_values(
        by=[
            "metrics.mean_f1",
            "metrics.std_f1",
            "metrics.recall",
            "metrics.precision",
        ],
        ascending=[False, True, False, False],
    ).iloc[0]

    run_id = selected["run_id"]
    mean_f1 = selected["metrics.mean_f1"]
    std_f1 = selected["metrics.std_f1"]
    test_f1 = selected["metrics.f1"]
    recall = selected["metrics.recall"]
    precision = selected["metrics.precision"]

    print(f"\nMLflow experiment: {experiment_name}")
    print("\nSelected model candidate:")
    print(f"Run ID: {run_id}")
    print(f"C: {selected['params.C']}")
    print(f"Mean CV F1: {mean_f1:.4f}")
    print(f"CV F1 Std: {std_f1:.4f}")
    print(f"Test F1: {test_f1:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"Precision: {precision:.4f}")

    print("\nRunning model quality gate...")

    checks = {
        "Mean CV F1": mean_f1 >= MIN_CV_F1,
        "Test F1": test_f1 >= MIN_TEST_F1,
        "Recall": recall >= MIN_RECALL,
    }

    for metric, passed in checks.items():
        print(f"{metric}: {'PASS' if passed else 'FAIL'}")

    if not all(checks.values()):
        print("\nModel quality gate FAILED.")
        print("Model will NOT be selected for registration.")
        sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(run_id)

    print("\nModel quality gate PASSED.")
    print(f"Selected run ID written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
