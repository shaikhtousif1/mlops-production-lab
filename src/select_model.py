import mlflow
import sys


MIN_CV_F1 = 0.60
MIN_TEST_F1 = 0.60
MIN_RECALL = 0.60


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

    # Select the best candidate
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

    mean_f1 = selected["metrics.mean_f1"]
    std_f1 = selected["metrics.std_f1"]
    test_f1 = selected["metrics.f1"]
    recall = selected["metrics.recall"]
    precision = selected["metrics.precision"]

    print("\nSelected model candidate:")
    print(f"Run ID: {run_id}")
    print(f"C: {selected['params.C']}")
    print(f"Mean CV F1: {mean_f1:.4f}")
    print(f"CV F1 Std: {std_f1:.4f}")
    print(f"Test F1: {test_f1:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"Precision: {precision:.4f}")

    # Quality gate
    print("\nRunning model quality gate...")

    checks = {
        "Mean CV F1": mean_f1 >= MIN_CV_F1,
        "Test F1": test_f1 >= MIN_TEST_F1,
        "Recall": recall >= MIN_RECALL,
    }

    for metric, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"{metric}: {status}")

    if not all(checks.values()):
        print("\nModel quality gate FAILED.")
        print("Model will NOT be registered.")
        sys.exit(1)

    print("\nModel quality gate PASSED.")

    # Output selected run ID for downstream processes
    print(f"\nSelected run ID: {run_id}")


if __name__ == "__main__":
    main()