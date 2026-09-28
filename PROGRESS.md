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

---

# Project Continuity Record

This section exists specifically so a future session can reconstruct the project state from the repository instead of relying on conversational memory.

## Source of truth

When continuing the project, inspect these in this order:

1. `PROGRESS.md` — current milestone and validated state.
2. `MLOPS_TEACHING_GUIDE.md` — executable learning path and known troubleshooting.
3. `.github/workflows/mlops-ci.yml` — current CI/CD implementation.
4. `src/` — actual application/training implementation.
5. `tests/` — executable quality contract.
6. `k8s/` — current Kubernetes desired state.
7. `Dockerfile` and `docker-compose.yml` — local/container execution model.
8. Git history — what changed and why when the current state is ambiguous.

Never assume an old conversational command is still correct if the repository differs.

## Learner profile and project objective

The learner already has strong infrastructure experience with AWS/Azure, Kubernetes, Docker, Terraform, GitOps/FluxCD and CI/CD. Therefore this lab is **not** intended to teach basic Kubernetes or cloud administration from scratch.

The learning objective is to build the missing MLOps mental model end-to-end:

```text
ML experiment
→ reproducible training
→ evaluation
→ model selection
→ model registry
→ model serving
→ application testing
→ containerization
→ image distribution
→ Kubernetes deployment
→ CI/CD
→ GitOps
→ observability
→ model/data lifecycle
```

The assistant should explain the ML-specific and MLOps-specific reasoning while avoiding unnecessary detours into infrastructure that the learner already understands.

## Current validated environment

The project has been exercised in:

- VS Code Dev Container
- Python 3.11.x
- Docker Desktop / WSL2 during local development
- disposable Kubernetes environments
- GitHub Actions
- GitHub Container Registry (GHCR)

The disposable Kubernetes environment used during validation had Kubernetes `v1.36.1` and successfully ran the API image pulled from GHCR.

## Important exact implementation facts

### Training

`src/train.py` uses Logistic Regression and writes two different model representations:

```text
model.pkl
  → joblib serialized sklearn model used by the API image

MLflow logged model under artifact path `model`
  → MLflow model representation used for experiment/registry learning
```

Do not conflate these two artifacts.

### Serving

`src/api.py` currently serves the packaged joblib model:

```python
model = joblib.load("model.pkl")
```

The API contract is:

```text
GET  /
POST /predict
```

Prediction inputs:

```text
age: int
tenure_months: int
monthly_charges: float
support_tickets: int
usage_hours: float
```

The response contains a class prediction:

```json
{"prediction": 1}
```

The exact class can vary with the trained model; the test contract is that a valid prediction is returned.

### CI

The current GitHub Actions workflow performs validation, training and model-quality selection before building and publishing the API image.

The current image tags are:

```text
ghcr.io/shaikhtousif1/customer-churn-api:${GITHUB_SHA}
ghcr.io/shaikhtousif1/customer-churn-api:latest
```

The next CI improvement is to consume the immutable Git-SHA image during deployment instead of relying on `latest`.

### Kubernetes

Current manifests contain one API Deployment and one ClusterIP Service. The Deployment currently uses the image reference:

```text
mlops-production-lab-api:latest
```

with:

```yaml
imagePullPolicy: Never
```

That setting was useful for the local Docker Desktop image-import exercise but is **not** the desired registry-based deployment model for the next phase. The next Kubernetes change should use the GHCR image and an immutable Git-SHA tag.

## Known failures and what they taught us

### MLflow local artifact failure

The MLflow metadata database contained the registered model/version and `production` alias, but `/mlartifacts` was empty. Loading:

```text
models:/customer-churn-model@production
```

therefore failed with:

```text
MlflowException: No such artifact: ''
```

Lesson: a model registry entry is metadata; the serving system still needs access to the actual model artifact.

Decision: do not spend additional learning time implementing local object storage. Treat durable artifact storage as a production-platform concern and move forward.

### Test import failure

Running:

```bash
pytest tests/test_api.py -v
```

initially produced:

```text
ModuleNotFoundError: No module named 'src'
```

Adding repository-root configuration through `pytest.ini` fixed the test discovery/import path.

Lesson: tests need a deterministic project import configuration, not a developer-specific shell environment.

### Wrong loader for model.pkl

An initial test tried:

```python
mlflow.pyfunc.load_model("model.pkl")
```

which failed because `model.pkl` did not contain an `MLmodel` directory structure.

Changing the test to `pickle.load()` also failed with:

```text
UnpicklingError: STACK_GLOBAL requires str
```

The training code showed the actual serialization method:

```python
joblib.dump(model, "model.pkl")
```

The correct loader was therefore:

```python
joblib.load("model.pkl")
```

This resulted in the complete suite passing:

```text
3 passed
```

Lesson: always inspect how an artifact was produced before choosing a loader.

### Local Docker image vs Kubernetes runtime

Kubernetes initially reported:

```text
ErrImageNeverPull
```

because the image existed in the local Docker environment but was not available to the Kubernetes container runtime.

The image was explicitly imported into the Docker Desktop Kubernetes runtime for the local exercise. Later, the same image was published to GHCR and pulled successfully from a disposable Kubernetes environment.

Lesson:

```text
Build location
  ≠
Container runtime
  ≠
Registry
```

The registry is the distribution boundary that makes CI/CD portable.

## What not to repeat unless the repository requires it

Do not restart or re-teach these already-completed detours merely because they appeared in older chat history:

- local MLflow artifact storage debugging
- MinIO/LocalStack setup
- Docker Desktop Kubernetes image-import mechanics
- basic `kubectl` concepts
- basic EKS/AKS concepts
- basic CI/CD concepts

Only revisit them if current repository state or a new failure requires it.

## Next exact milestone

The next implementation milestone is:

```text
CI build/test
    ↓
Build immutable GHCR image
    ↓
Deploy Git-SHA image to disposable Kubernetes
    ↓
Wait for rollout
    ↓
Run API smoke test
    ↓
Capture deployment evidence
```

After that:

```text
GitOps with FluxCD
    ↓
Observability
    ↓
MLOps-specific monitoring
    ↓
Drift/retraining/promotion
```

Do not jump to AWS/Azure yet. The learner already understands cloud Kubernetes; the value now is proving the MLOps delivery lifecycle first.

## Session-start protocol

When a new session begins, use this protocol before giving implementation commands:

```text
1. Read PROGRESS.md.
2. Read the relevant section of MLOPS_TEACHING_GUIDE.md.
3. Inspect the current GitHub tree/files needed for the next task.
4. Check the latest commit on main.
5. Identify the last completed milestone.
6. Identify the first unfinished milestone.
7. State that checkpoint briefly.
8. Give only the commands needed for the next checkpoint.
```

If the repository contradicts an old conversation message, trust the repository and explicitly call out the difference.
