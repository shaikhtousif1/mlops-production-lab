# MLOps Production Lab — Progress

## Checkpoint — 2026-09-28

The lab has moved from ML experimentation into a working **model → API → container → registry → Kubernetes** path. The next focus is deployment automation, not more local infrastructure.

## Current end-to-end state

```text
Dataset
  ↓
Training + cross-validation
  ↓
MLflow tracking
  ↓
Deterministic model selection
  ↓
Model Registry
  ↓
FastAPI inference API
  ↓
Automated tests
  ↓
Docker image
  ↓
GHCR
  ↓
Kubernetes
  ↓
API smoke test
```

## Completed

- [x] VS Code Dev Container / Python 3.11
- [x] Reproducible synthetic customer-churn dataset v2
- [x] Logistic Regression with configurable `C`
- [x] 5-fold cross-validation
- [x] Accuracy / Precision / Recall / F1 / ROC-AUC
- [x] MLflow experiment tracking
- [x] Dataset lineage using `dataset_version=v2`
- [x] Deterministic model selection
- [x] MLflow Model Registry
- [x] `customer-churn-model` version 1
- [x] `production` alias verification
- [x] FastAPI `/` and `/predict`
- [x] Dockerized API
- [x] Docker Compose development stack
- [x] PostgreSQL-backed MLflow metadata
- [x] API tests and model test
- [x] `pytest.ini`
- [x] Full test suite: **3/3 passed**
- [x] GitHub Actions CI: validation, tests, training, quality gate, registration, image build/push
- [x] GHCR image: `ghcr.io/shaikhtousif1/customer-churn-api`
- [x] Kubernetes Deployment + Service
- [x] Readiness/liveness probes
- [x] Resource requests/limits
- [x] Kubernetes inference smoke test

## Important serving decision

The local PostgreSQL-backed MLflow setup exposed an artifact-storage problem: registry metadata existed, but the local model artifact was not available where the API needed it.

We deliberately stopped debugging local artifact plumbing and used a teaching shortcut:

```text
MLflow → tracking / registry learning
model.pkl → packaged into API image → FastAPI
```

This is **not** the final production architecture. A real platform would use durable artifact/object storage or a controlled model build/deployment process.

## Model artifact lesson

`src/train.py` creates the local serving artifact with:

```python
joblib.dump(model, "model.pkl")
```

Therefore it is loaded with:

```python
joblib.load("model.pkl")
```

It is not an MLflow model directory and must not be loaded with `mlflow.pyfunc.load_model("model.pkl")`.

## Testing

```text
tests/
├── test_api.py
└── test_model.py
```

Run:

```bash
pytest -v
```

Expected current result:

```text
3 passed
```

`pytest.ini` adds the repository root to Python's path and points pytest at `tests/`.

## GHCR

The API image is published as:

```text
ghcr.io/shaikhtousif1/customer-churn-api
```

The disposable Kubernetes environment successfully pulled and ran the image.

GitHub Actions publishes both a Git-SHA tag and `latest`:

```text
ghcr.io/${OWNER}/customer-churn-api:${GITHUB_SHA}
ghcr.io/${OWNER}/customer-churn-api:latest
```

Next improvement: deploy the immutable Git-SHA tag instead of `latest`.

## Kubernetes

```text
k8s/
├── deployment.yaml
└── service.yaml
```

Current deployment:

```text
customer-churn-api
replicas: 1
containerPort: 8000
```

Health checks:

```text
readiness → GET /
liveness  → GET /
```

Resources:

```text
requests: 100m CPU / 128Mi
limits:   500m CPU / 512Mi
```

Validation:

```bash
kubectl get nodes
kubectl get pods
kubectl get services
kubectl port-forward service/customer-churn-api 8001:8000
curl http://localhost:8001/
curl -X POST "http://localhost:8001/predict?age=45&tenure_months=24&monthly_charges=80&support_tickets=2&usage_hours=150"
```

Observed prediction:

```json
{"prediction":1}
```

## Current CI pipeline

```text
Checkout
  ↓
Python 3.11
  ↓
Install dependencies
  ↓
py_compile
  ↓
pytest
  ↓
Training
  ↓
Quality gate
  ↓
Model registration
  ↓
GHCR login
  ↓
Docker build + push
```

Deployment is intentionally the next task.

## Deliberately deferred

- AWS/Azure resources
- paid infrastructure
- local MinIO/LocalStack artifact-storage work
- production secrets management
- production object storage

The disposable Kubernetes environment is sufficient for the next learning stage.

## Next phase

### CI-driven deployment

```text
Git push
   ↓
GitHub Actions
   ↓
pytest
   ↓
quality gate
   ↓
Docker build
   ↓
GHCR
   ↓
Kubernetes deployment
   ↓
rollout verification
   ↓
API smoke test
```

### Then GitOps

```text
Git repository
   ↓
Kubernetes desired state
   ↓
FluxCD
   ↓
Kubernetes reconciliation
```

### Later production concerns

- immutable image/model versions
- rollback
- secrets
- observability
- API metrics
- model/data drift
- retraining
- model promotion

Cloud deployment comes after the workflow is understood in the disposable environment.

## Working principle

```text
Problem
  ↓
Failure / limitation
  ↓
Why it matters in production
  ↓
Smallest useful fix
  ↓
Hands-on validation
  ↓
Production equivalent
```
