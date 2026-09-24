import mlflow

runs = mlflow.search_runs()

# Only consider the current dataset version
runs = runs[
    runs["tags.dataset_version"] == "v2"
]

# Only consider runs that contain CV F1 results
candidates = runs.dropna(
    subset=["metrics.mean_f1"]
)

# Select based on cross-validation performance
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

print("Selected model candidate:")
print(f"Run ID: {selected['run_id']}")
print(f"C: {selected['params.C']}")
print(f"Mean CV F1: {selected['metrics.mean_f1']:.4f}")
print(f"CV F1 Std: {selected['metrics.std_f1']:.4f}")
print(f"Test F1: {selected['metrics.f1']:.4f}")
print(f"Recall: {selected['metrics.recall']:.4f}")
print(f"Precision: {selected['metrics.precision']:.4f}")