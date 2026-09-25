# MLOps Production Lab — Progress

## Current checkpoint — 2026-09-25

### Career / learning direction

Target progression:
- DevOps / Cloud
- MLOps
- LLMOps
- FDE

The project is intentionally being built as a production-style MLOps lab rather than as a pure Data Science exercise. ML concepts are being learned deeply enough to understand the ML Engineer ↔ MLOps handoff, while the project progressively shifts toward automation, deployment, infrastructure, CI/CD, observability, and production operations.

---

## Environment

- GitHub repo: `shaikhtousif1/mlops-production-lab`
- Active development environment: VS Code Dev Container
- Base image: Python 3.11
- Docker Desktop + WSL2 integration working
- MLflow: 3.16.1
- Docker Compose: available on the WSL host
- Development workflow is intentionally host/container separated:
  - Dev Container → Python development, training, MLflow client work and MLOps workloads
  - WSL host → Docker Engine/Compose and GitHub operations
- Personal SSH credentials are not copied into the Dev Container.

### Development architecture

```text
Windows
  └── WSL2
       ├── Git / GitHub SSH
       ├── Docker Engine
       └── Project repository
             ↕ bind mount
          Dev Container
             ├── Python 3.11
             ├── scikit-learn
             ├── MLflow
             └── Training / selection code
```

MLflow runs are **experiment runs**, not Docker containers. One development environment can create many MLflow runs with different parameters.

---

# ML project

## Project

Customer churn prediction.

## Dataset evolution

The original dataset contained only 20 synthetic customer records and produced approximately 100% accuracy/F1 for multiple Logistic Regression configurations.

This was useful for learning the mechanics, but it was not useful for meaningful model selection.

### Dataset v1

Original dataset preserved as:

```text
data/customers_v1.csv
```

### Dataset v2

Generated a new synthetic dataset:

```text
data/customers.csv
```

Characteristics:
- 1,000 customer records
- Features: `age`, `tenure_months`, `monthly_charges`, `support_tickets`, `usage_hours`
- Target: `churned`
- Class distribution: 524 non-churn / 476 churn
- Churn rate: 47.6%

Added reproducible dataset generator:

```text
src/generate_data.py
```

The generator uses a fixed random seed (`42`) so the dataset can be recreated consistently.

### Why the dataset was changed

The original dataset made almost every model configuration look perfect. That prevented meaningful learning around model comparison, error analysis, metric trade-offs and experiment selection.

The new dataset introduces noise and class overlap so the evaluation pipeline produces realistic, imperfect results.

---

# Training and evaluation workflow

Current model:
- scikit-learn Logistic Regression
- configurable `C` parameter
- `max_iter=1000`
- 80/20 train/test split
- `random_state=42`
- stratified split

Example:

```bash
python src/train.py --c 0.1
```

The workflow evaluates:
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

A previous bug used probability output as the predictions array, causing a shape mismatch. This was corrected.

---

# MLflow experiment tracking

MLflow tracks parameters:
- model_type
- C
- max_iter
- test_size
- random_state

Metrics:
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

This was necessary because the MLflow database contained historical runs from Dataset v1. Without filtering by dataset version, the selector incorrectly selected an old Dataset v1 run with F1/precision/recall of 1.0.

Lesson:

> MLflow runs from different dataset versions should not be blindly compared. Experiment lineage and dataset version are part of model selection.

---

# Hyperparameter experiment

Tested Logistic Regression `C` values:

```text
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

---

# Model selection

Added:

```text
src/select_model.py
```

The selector:
1. Filters to `dataset_version=v2`.
2. Ignores incomplete runs without CV F1.
3. Selects using the hierarchy:
   1. Highest mean CV F1
   2. Lowest CV F1 standard deviation
   3. Highest recall
   4. Highest precision

Current selected candidate:

```text
Run ID: c6036648639745789ae51a102a8b5e0a
C: 0.1
Mean CV F1: 0.6187
CV F1 Std: 0.0436
Test F1: 0.6243
Recall: 0.6211
Precision: 0.6277
```

The selector is a deterministic policy. It does not imply that C=0.1 is statistically or practically superior given the very small metric differences.

### Why selection was changed

Initially the selector used final test-set F1. We changed this because repeatedly selecting/tuning models against the final test set can turn the test set into an implicit tuning dataset.

Current conceptual flow:

```text
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

The final test set is treated as final evaluation rather than the primary tuning mechanism.

---

# Model Registry and serving

The selected model was registered earlier as:

```text
customer-churn-model
Version: 1
```

A prediction script was added and successfully loaded:

```text
models:/customer-churn-model/1
```

Example prediction returned churn class `1` for a sample customer.

A FastAPI inference service was then added in `src/api.py` with:
- `GET /` health endpoint
- `POST /predict` inference endpoint
- configurable `MLFLOW_TRACKING_URI`
- configurable `MODEL_URI`
- MLflow model loading via `mlflow.pyfunc.load_model`

Swagger/OpenAPI was used to test the API interactively.

---

# Containerization

The inference service was containerized using the root `Dockerfile`.

The API image contains the application dependencies from `requirements.txt`, including:
- pandas
- scikit-learn
- MLflow 3.16.1
- FastAPI
- Uvicorn

The MLflow server gets a separate image under:

```text
mlflow/Dockerfile
```

It extends the MLflow 3.16.1 image and installs:
- `psycopg2-binary` for PostgreSQL connectivity
- `boto3` for future S3 artifact storage

---

# Docker Compose production-style architecture

A Docker Compose stack was introduced to move beyond the original single-container/dev-container setup.

Current services:

```text
                    Docker Compose
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   PostgreSQL          MLflow          FastAPI
     :5432              :5000            :8000
        │                │                │
        │                ├── Tracking     │
        │                ├── Registry     │
        │                └── Artifacts    │
        │                                 │
        └─────────────────────────────────┘
```

Current Compose services:
- `postgres` → persistent MLflow backend metadata and registry
- `mlflow` → tracking server and model registry
- `api` → model inference service

Persistent Docker volumes:
- `postgres_data`
- `mlflow_artifacts`

The current MLflow server uses PostgreSQL as the backend store and a Docker volume for artifacts.

### Why PostgreSQL was introduced

The original development setup used local SQLite/file-based MLflow state. That is appropriate for learning and local experimentation but does not represent the shared-server architecture normally used by a team.

The new stack separates:

```text
PostgreSQL
    ↓
MLflow metadata / experiments / registry

MLflow artifact volume
    ↓
Model artifacts
```

This separation is an important MLOps architecture concept.

### LocalStack/MinIO detour

We initially attempted to introduce MinIO and then LocalStack as local S3-compatible storage. Both introduced registry/licensing/image availability issues in the current environment. Rather than spending learning time on tool-specific plumbing, the stack was simplified to a persistent MLflow artifact volume.

The intended production evolution remains:

```text
Local artifact volume
        ↓
S3-compatible object storage
        ↓
AWS S3 in production
```

The MLflow Docker image already includes `boto3` so the later S3 transition is straightforward.

---

# Docker Compose concepts learned

Important distinction:

### Dockerfile
Defines how to build one image.

Example:

```text
Dockerfile
   ↓
customer-churn-api image
```

### Docker Compose
Defines how multiple containers/services work together.

Example:

```text
compose
 ├── PostgreSQL
 ├── MLflow
 └── FastAPI
```

### `depends_on`
Controls startup ordering/conditions. PostgreSQL is marked healthy before MLflow starts.

### Volumes
Persist state outside the disposable container filesystem.

```text
postgres_data
mlflow_artifacts
```

### Container networking
Compose gives services a shared network, so the API can reach MLflow using:

```text
http://mlflow:5000
```

rather than `localhost`.

---

# ML Engineer vs MLOps distinction learned

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

The project intentionally performed enough ML work to understand this boundary. The next phase should increasingly emphasize the MLOps side.

---

# Important lessons learned

## 1. Experiment runs are not containers

An MLflow run represents one execution of an experiment. A Docker/Dev Container is the runtime environment.

One environment can produce many MLflow runs:

```text
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

61.87% vs 61.61% CV F1 is only 0.26 percentage points. A deterministic selector can choose one model without claiming that the difference is meaningful.

## 4. Model selection needs a predefined policy

```text
Mean CV F1
    ↓
CV F1 stability
    ↓
Recall
    ↓
Precision
```

This makes selection reproducible and auditable.

## 5. Test-set results should be treated carefully

The test set should provide final evaluation rather than becoming a repeatedly tuned decision mechanism.

## 6. Containers are not persistence

Containers are replaceable runtime units. Persistent state belongs in databases, object storage, or volumes designed for persistence.

## 7. Service health matters more than `compose up` returning success

A Compose deployment can create containers while one or more services immediately exit. Always validate with:

```bash
docker compose ps -a
docker compose logs <service>
```

## 8. Production architecture is an evolution, not a single tool

The current stack is intentionally moving through layers:

```text
Python training
   ↓
MLflow tracking
   ↓
Model Registry
   ↓
FastAPI
   ↓
Docker
   ↓
Docker Compose
   ↓
Kubernetes
   ↓
CI/CD + GitOps
   ↓
Monitoring + retraining
```

---

# Git checkpoint

Latest pushed commit:

```text
42826525533a18aa6cd51338e07bc3e73b0be2b8
Build containerized MLOps serving stack
```

Previous important checkpoints:

```text
2627bd0  Improve model evaluation and selection
af962ec  Update MLOps learning progress
4977a38  Add configurable experiments and cross-validation
7a84edf  Add churn training and MLflow tracking
ee87ec1  Add development container
```

The latest repository contains the containerized MLOps serving stack, Compose configuration, MLflow PostgreSQL integration, and API configuration.

### Cleanup item

`tmp/check_mlflow.py` was a temporary inspection script and should be removed in a later cleanup commit.

Generated state remains excluded from Git:

```text
mlflow.db
mlruns/
mlartifacts/
```

Do not reset/amend historical checkpoints just for cleanup; handle cleanup as a separate commit.

---

# Current status — end of 2026-09-25 session

### Completed

- [x] Development container
- [x] Synthetic churn dataset v2
- [x] Reproducible data generation
- [x] Logistic Regression training
- [x] Cross-validation
- [x] Evaluation metrics
- [x] Dataset lineage tag
- [x] Model comparison
- [x] Deterministic model selection
- [x] MLflow Model Registry introduction
- [x] Prediction script
- [x] FastAPI inference API
- [x] Swagger/OpenAPI testing
- [x] API Docker image
- [x] MLflow Docker image with PostgreSQL driver
- [x] Docker Compose stack
- [x] PostgreSQL-backed MLflow
- [x] Persistent MLflow artifact volume
- [x] API → MLflow configuration through environment variables
- [x] Local Compose stack successfully running with PostgreSQL, MLflow and FastAPI containers

### Not yet completed

- [ ] Bootstrap/register the selected model in the new PostgreSQL-backed MLflow environment
- [ ] Make model version selection configurable rather than hardcoded to version `1`
- [ ] Production-grade secrets management
- [ ] S3 artifact storage
- [ ] CI pipeline
- [ ] Automated image build/push
- [ ] Kubernetes deployment
- [ ] GitOps
- [ ] Inference observability
- [ ] Model/data drift monitoring
- [ ] Automated retraining
- [ ] Promotion/rollback workflow

---

# Next phase

The project should now move decisively toward MLOps engineering rather than adding more manual model experiments.

Planned sequence:

```text
Selected model
      ↓
MLflow Model Registry in shared PostgreSQL-backed environment
      ↓
Model version / promotion strategy
      ↓
CI pipeline
      ↓
Container image build + registry
      ↓
Kubernetes deployment
      ↓
GitOps
      ↓
Monitoring / alerting
      ↓
Drift detection
      ↓
Retraining / promotion / rollback
```

---

## Working principle

Learn by:

```text
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
