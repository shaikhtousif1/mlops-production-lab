# MLOps Production Lab — Progress

## Current checkpoint — 2026-09-24

### Career / learning direction

Target progression:
- DevOps / Cloud
- MLOps
- LLMOps
- FDE

The project is intentionally being built as a production-style MLOps lab rather than as a pure Data Science exercise. ML concepts are being learned deeply enough to understand the ML Engineer ↔ MLOps handoff, while the project will progressively shift toward automation, deployment, infrastructure, CI/CD, observability, and production operations.

---

## Environment

- GitHub repo: shaikhtousif1/mlops-production-lab
- Active development environment: VS Code Dev Container
- Base image: Python 3.11
- Docker Desktop + WSL2 integration working
- MLflow: 3.16.1
- Development workflow is intentionally host/container separated:
  - Dev Container → Python development, training, MLflow and MLOps workloads
  - WSL/macOS host → GitHub authentication and Git operations
- Personal SSH credentials are not copied into the Dev Container.

### Current local architecture

```
Windows
  └── WSL2
       ├── Git / GitHub SSH
       └── Project repository
             ↕ bind mount
          Dev Container
             ├── Python
             ├── scikit-learn
             ├── MLflow
             └── Training / selection code
```

MLflow runs are **experiment runs**, not Docker containers. The current Dev Container is the runtime environment in which the training process and local MLflow UI/server run.

Current local MLflow storage is file-based/local:
- `mlflow.db`
- MLflow artifact/run directories

These are local development state and should not be committed to Git.

---

# ML project

## Project

Customer churn prediction.

## Dataset evolution

The original dataset contained only 20 synthetic customer records and produced approximately 100% accuracy/F1 for multiple Logistic Regression configurations.

This was useful for learning the mechanics, but it was not useful for meaningful model selection.

### Dataset v1

Original dataset preserved as:

```
data/customers_v1.csv
```

### Dataset v2

Generated a new synthetic dataset:

```
data/customers.csv
```

Characteristics:
- 1,000 customer records
- Features:
  - age
  - tenure_months
  - monthly_charges
  - support_tickets
  - usage_hours
- Target:
  - churned
- Class distribution:
  - 524 non-churn
  - 476 churn
  - 47.6% churn rate

Added reproducible dataset generator:

```
src/generate_data.py
```

The generator uses a fixed random seed (`42`) so the dataset can be recreated consistently.

### Why the dataset was changed

The original dataset made almost every model configuration look perfect. That prevented us from learning meaningful:
- model comparison
- error analysis
- metric trade-offs
- experiment selection

The new dataset introduces noise and class overlap so the evaluation pipeline produces realistic, imperfect results.

---

# Training workflow

Current model:
- scikit-learn Logistic Regression
- configurable `C` parameter
- `max_iter=1000`
- 80/20 train/test split
- `random_state=42`
- stratified split

Run example:

```bash
python src/train.py --c 0.1
```

---

# Model evaluation

The training workflow now evaluates:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- 5-fold CV Accuracy
- 5-fold CV Accuracy standard deviation
- 5-fold CV F1
- 5-fold CV F1 standard deviation

Important distinction:

- `predict(X_test)` → hard 0/1 predictions used for accuracy, precision, recall, F1 and confusion matrix.
- `predict_proba(X_test)[:, 1]` → class-1 probabilities used for ROC-AUC.

A previous bug used probability output as the predictions array, causing a shape mismatch. This was corrected and reinforced the distinction between classification decisions and probability ranking.

---

# MLflow experiment tracking

MLflow tracks:

### Parameters

- model_type
- C
- max_iter
- test_size
- random_state

### Metrics

- accuracy
- precision
- recall
- f1
- roc_auc
- mean_accuracy
- std_accuracy
- mean_f1
- std_f1

The trained Logistic Regression model is logged as an MLflow model artifact.

### Dataset versioning

Added:

```python
mlflow.set_tag("dataset_version", "v2")
```

This was necessary because the MLflow database contained historical runs from Dataset v1.

Without filtering by dataset version, the model selector incorrectly selected an old Dataset v1 run with F1/precision/recall of 1.0.

Lesson:

> MLflow runs from different dataset versions should not be blindly compared. Experiment lineage and dataset version are part of model selection.

---

# Hyperparameter experiment

Tested five Logistic Regression `C` values:

```
0.01
0.1
1
10
100
```

Approximate CV-F1 results:

| C | Mean CV F1 | CV F1 Std |
|---:|---:|---:|
| 0.01 | 61.61% | 4.54% |
| 0.1 | 61.87% | 4.36% |
| 1 | 61.57% | 3.96% |
| 10 | 61.57% | 3.96% |
| 100 | 61.57% | 3.96% |

Interpretation:

- C=0.1 has the highest observed mean CV F1.
- The difference is very small.
- There is no strong evidence that C=0.1 is materially better than the other configurations.
- The experiment demonstrates that the highest metric does not automatically imply a practically significant improvement.
- Changing C is not a particularly powerful lever for this dataset/model combination.

The current selected candidate is therefore a **policy-based selection**, not a claim of a statistically or practically significant superiority.

---

# Model selection

Added:

```
src/select_model.py
```

The selector:

1. Filters to `dataset_version=v2`.
2. Ignores incomplete runs without CV F1.
3. Selects using the following hierarchy:
   1. Highest mean CV F1
   2. Lowest CV F1 standard deviation
   3. Highest recall
   4. Highest precision

Current selected candidate:

```
Run ID: c6036648639745789ae51a102a8b5e0a
C: 0.1
Mean CV F1: 0.6187
CV F1 Std: 0.0436
Test F1: 0.6243
Recall: 0.6211
Precision: 0.6277
```

### Why selection was changed

Initially the selector used final test-set F1. We changed this because repeatedly selecting/tuning models against the final test set can turn the test set into an implicit tuning dataset.

Current conceptual flow:

```
Training data
    ↓
5-fold cross-validation
    ↓
Mean CV F1
    ↓
Model selection
    ↓
Final test-set evaluation
```

The final test set is therefore treated as a final evaluation rather than the primary tuning mechanism.

---

# ML Engineer vs MLOps distinction learned

A key discussion during this phase was that much of the manual model experimentation is primarily ML Engineer/Data Scientist work.

### ML Engineer typically owns

- Feature engineering
- Model selection strategy
- Model architecture
- Hyperparameter tuning
- Evaluation methodology
- Business metric interpretation
- Model quality requirements

### MLOps typically owns/enables

- Reproducible training execution
- Experiment tracking infrastructure
- Model Registry
- Training automation
- CI/CD
- Model packaging
- Model serving infrastructure
- Kubernetes/cloud deployment
- Monitoring
- Drift detection
- Retraining workflows
- Promotion/rollback automation

The project intentionally performed enough ML work to understand this boundary.

The next phase should shift the emphasis toward the MLOps side.

---

# Important lessons learned

## 1. Experiment runs are not containers

An MLflow run represents one execution of an experiment.

A Docker/Dev Container is the runtime environment.

One Dev Container can produce many MLflow runs:

```
Dev Container
  ├── MLflow Run: C=0.01
  ├── MLflow Run: C=0.1
  ├── MLflow Run: C=1
  ├── MLflow Run: C=10
  └── MLflow Run: C=100
```

## 2. Dataset lineage matters

A model trained on Dataset v1 should not automatically be compared with a model trained on Dataset v2.

## 3. Metric precision is not practical significance

For example:

- 61.87% vs 61.61% CV F1

is a difference of only 0.26 percentage points.

The pipeline can select one model deterministically without claiming that the difference is meaningful.

## 4. Model selection needs a predefined policy

We defined the selection policy before using it:

```
Mean CV F1
    ↓
CV F1 stability
    ↓
Recall
    ↓
Precision
```

This makes the selection reproducible and auditable.

## 5. Test-set results should be treated carefully

The test set should provide the final evaluation rather than becoming a repeatedly tuned decision mechanism.

---

# Git checkpoint

Latest pushed commit:

```
2627bd0
Improve model evaluation and selection
```

Remote branch:
- `main`
- Successfully pushed to GitHub.

Files included in the latest commit:

```
data/customers.csv
data/customers_v1.csv
src/generate_data.py
src/select_model.py
src/train.py
tmp/check_mlflow.py
```

### Cleanup item

`tmp/check_mlflow.py` was a temporary inspection script and should be removed in the next cleanup commit.

Also verify that generated MLflow state such as:

```
mlflow.db
mlruns/
mlartifacts/
```

is excluded by `.gitignore` and is not committed.

Do not amend/reset the current checkpoint just for this cleanup; handle it as a separate cleanup commit.

---

# Next phase

## MLflow Model Registry

The next objective is to move from:

> "We trained and selected a model."

to:

> "We have a versioned model with a controlled lifecycle that can be promoted toward production."

Planned sequence:

```
Selected model
      ↓
MLflow Model Registry
      ↓
Model versioning
      ↓
Model lifecycle / promotion
      ↓
CI/CD
      ↓
Containerized inference API
      ↓
Kubernetes deployment
      ↓
Monitoring
      ↓
Retraining / rollback
```

The project should now progressively shift from manual ML experimentation toward production MLOps engineering.

---

## Working principle

Learn by:

```
Problem
   ↓
Pain / failure mode
   ↓
Why the problem matters
   ↓
Tool / pattern
   ↓
Implementation
   ↓
Validation
   ↓
Productionization
```

Keep GitHub as the source of truth so the project can be resumed from another machine. Keep developer credentials out of application containers unless there is a concrete need.
