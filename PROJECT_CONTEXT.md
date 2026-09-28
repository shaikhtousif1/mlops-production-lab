# MLOps Production Lab — Persistent Project Context

This file is a compact continuity record for future sessions. It exists so the project can be resumed from repository state rather than relying on chat history.

## 1. Project objective

Build a realistic MLOps lifecycle around a small customer-churn model while avoiding unnecessary cloud spend.

The learner already has strong experience with:

- AWS / Azure
- Kubernetes
- Docker
- Terraform
- CI/CD
- GitOps / FluxCD

Therefore the project should focus on the **MLOps-specific lifecycle and reasoning**, not re-teaching basic infrastructure.

Target lifecycle:

```text
Data
 → Training
 → Evaluation
 → Experiment tracking
 → Model selection
 → Model registry
 → Serving
 → Testing
 → Containerization
 → Image registry
 → Kubernetes
 → CI/CD
 → GitOps
 → Observability
 → Drift / retraining / promotion
```

Cloud deployment to EKS/AKS is intentionally deferred until the lifecycle is understood in a disposable environment.

## 2. Current checkpoint

As of 2026-09-28, the following path has been validated:

```text
Training
 → MLflow tracking
 → deterministic model selection
 → Model Registry
 → FastAPI
 → pytest
 → Docker
 → GHCR
 → disposable Kubernetes
 → prediction smoke test
```

Current test result:

```text
3 passed
```

The Kubernetes API has been successfully reached through a port-forward and returned a valid prediction.

## 3. Current repository components

```text
.github/workflows/mlops-ci.yml   CI validation/training/registration/image publishing
src/train.py                     model training + MLflow logging + model.pkl
src/select_model.py              deterministic quality gate
src/register_model.py            Model Registry registration
src/predict.py                   prediction utility
src/api.py                       FastAPI serving joblib model
model.pkl                        serialized sklearn model used by API
k8s/deployment.yaml              Kubernetes Deployment
k8s/service.yaml                 ClusterIP Service
tests/test_api.py                API tests
tests/test_model.py              model loading/prediction test
pytest.ini                       pytest import/test configuration
Dockerfile                       API image
docker-compose.yml               local MLflow/Postgres/API stack
requirements.txt                 Python dependencies
PROGRESS.md                      milestone/state record
MLOPS_TEACHING_GUIDE.md          executable hands-on workbook
```

## 4. Important model-artifact distinction

The training code creates two conceptually different artifacts:

### Serving artifact

```python
joblib.dump(model, "model.pkl")
```

The FastAPI application loads it with:

```python
joblib.load("model.pkl")
```

### MLflow artifact

Training also calls:

```python
mlflow.sklearn.log_model(model, "model")
```

This is an MLflow model representation and is different from `model.pkl`.

Do not try to load `model.pkl` using:

```python
mlflow.pyfunc.load_model("model.pkl")
```

That caused the earlier `Could not find an MLmodel configuration file` error.

Trying `pickle.load()` also failed because the file was serialized using joblib. The correct loader is `joblib.load()`.

## 5. MLflow artifact-storage detour

The local PostgreSQL-backed MLflow setup successfully stored registry metadata, including:

```text
customer-churn-model
version: 1
alias: production
```

but the `/mlartifacts` volume was empty. Loading the registered model therefore failed with:

```text
MlflowException: No such artifact: ''
```

This is a real production concept: registry metadata does not replace access to the underlying model artifact.

However, the project intentionally does **not** spend more learning time building MinIO/LocalStack or other local artifact infrastructure.

Current teaching shortcut:

```text
MLflow → tracking / registry concepts
model.pkl → packaged into API image → serving
```

A production platform would normally use durable object/artifact storage and a controlled model packaging/promotion workflow.

## 6. Testing history

The API tests initially failed with:

```text
ModuleNotFoundError: No module named 'src'
```

The repository now uses `pytest.ini` so tests run from the repository root without requiring a developer-specific `PYTHONPATH`.

The model test initially attempted MLflow loading and then raw pickle loading. The training implementation was inspected to identify `joblib.dump`, and the test was corrected to use `joblib.load`.

Final validated result:

```text
pytest -v
→ 3 passed
```

Do not re-open these issues unless current repository state shows a regression.

## 7. Container and Kubernetes history

The API image is published to:

```text
ghcr.io/shaikhtousif1/customer-churn-api
```

The disposable Kubernetes environment successfully pulled this image and ran the API.

Earlier Docker Desktop Kubernetes testing produced:

```text
ErrImageNeverPull
```

because the local Docker image was not automatically available to the Kubernetes runtime. The image had to be imported into the runtime.

This taught the important distribution concept:

```text
local Docker image
 ≠
Kubernetes runtime image
```

The registry solves this distribution problem.

## 8. Important current Kubernetes caveat

The current committed `k8s/deployment.yaml` originated from the local Docker Desktop exercise and uses a local image reference / `imagePullPolicy: Never`.

For the **next deployment milestone**, change the Deployment to consume the public GHCR image using an immutable Git-SHA tag.

Do not keep using `latest` for automated deployment.

Target form:

```text
ghcr.io/shaikhtousif1/customer-churn-api:<GITHUB_SHA>
```

The next deployment workflow should prove that CI can publish an image and a disposable Kubernetes environment can pull that exact image.

## 9. Current CI boundary

The GitHub Actions workflow currently does approximately:

```text
Checkout
 → Python setup
 → dependency installation
 → syntax validation
 → pytest
 → training
 → quality gate
 → model registration
 → GHCR login
 → Docker build/push
```

This is currently **CI**, not complete CD.

The next milestone is:

```text
CI
 → immutable image push
 → Kubernetes deployment
 → rollout verification
 → API smoke test
```

After that, introduce FluxCD/GitOps.

## 10. Next milestone — do this next

### Phase A: CI-driven Kubernetes deployment

Goal:

```text
Git push
   ↓
GitHub Actions
   ↓
pytest / quality gate
   ↓
Build image
   ↓
Push GHCR image tagged with Git SHA
   ↓
Deploy exact Git-SHA image to disposable Kubernetes
   ↓
Wait for rollout
   ↓
Smoke test /
   ↓
Smoke test /predict
```

The deployment should use the immutable SHA tag, not `latest`.

### Phase B: GitOps

Once Phase A works:

```text
Git repository
   ↓
desired Kubernetes state
   ↓
FluxCD
   ↓
Kubernetes reconciliation
```

The learner already has working knowledge of FluxCD, so the teaching focus should be on **why GitOps matters for an ML service** and how model/application versioning interacts with desired state.

### Phase C: MLOps-specific operations

Then cover:

- application metrics
- inference latency/error rate
- prediction distribution
- model performance monitoring
- data drift
- model drift
- retraining trigger
- model promotion
- rollback
- lineage between dataset, training run, model version and image version

### Phase D: Cloud mapping

Only after the disposable lifecycle works, map the architecture to AWS/Azure:

```text
GHCR / ECR / ACR
Kubernetes / EKS / AKS
GitHub Actions / Azure DevOps
FluxCD
Object storage
Secrets
Observability
```

No paid cloud resources are required to learn the preceding phases.

## 11. Session-start protocol

When resuming this project in a new chat/session, the assistant should:

1. Read `PROGRESS.md`.
2. Read the relevant part of `MLOPS_TEACHING_GUIDE.md`.
3. Read this file.
4. Inspect the current repository files relevant to the next milestone.
5. Check the latest commit on `main`.
6. Verify whether the repository has changed since the last checkpoint.
7. Identify the first unfinished milestone.
8. Briefly state the checkpoint.
9. Give only the commands required for the next checkpoint.
10. Do not repeat already-completed troubleshooting unless the current state requires it.

Repository state wins over old chat instructions if they conflict.

## 12. Teaching style for this project

For every major step, explain four things:

```text
What we are doing
Why we need it
What production problem it represents
How we validate it
```

Use the smallest implementation that teaches the production concept.

Do not introduce infrastructure merely because it exists in a real production platform.

The learner explicitly wants a hands-on workbook that another engineer could execute independently, so commands should include expected validation and troubleshooting where useful.

## 13. Anti-hallucination rule

Never assume a tool, file, configuration, version, image tag, Kubernetes state, model version or CI result from an old conversation.

Verify it from the current repository or current tool output before making it a factual statement.

If something is unknown, say it is unknown and inspect the repository before proposing the next change.

If current repository state differs from the workbook, update the workbook rather than silently pretending they match.

## 14. Current stop point

The learner intentionally paused after proving:

```text
pytest → 3/3 passed
Docker API → working
GHCR → image available
Kubernetes → API running
Kubernetes smoke test → prediction returned
```

The next session should start at **CI-driven Kubernetes deployment using an immutable Git-SHA image**.
