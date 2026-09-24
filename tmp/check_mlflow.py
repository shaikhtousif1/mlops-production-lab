import mlflow

runs = mlflow.search_runs()

print("\nAvailable columns:")
print(runs.columns.tolist())

print("\nRelevant experiment data:")
print(
    runs[
        [
            "run_id",
            "params.C",
            "metrics.f1",
            "metrics.precision",
            "metrics.recall",
            "metrics.roc_auc",
        ]
    ]
)