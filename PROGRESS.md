# MLOps Production Lab — Progress

## Checkpoint — 2026-09-29

The lab has moved beyond basic model training and API deployment into the **model promotion → packaging → immutable image → GitOps** boundary.

The latest repository state implements the following intended lifecycle:

```text
Dataset
  ↓
Training + cross-validation
  ↓
MLflow tracking
  ↓
Deterministic quality gate / selection
  ↓
MLflow Model Registry
  ↓
Production alias
  ↓
Package EXACT promoted model
  ↓
model.pkl + model_metadata.json
  ↓
Docker image
  ↓
GHCR
  ↓
Kubernetes desired state
  ↓
Flux reconciliation
```

## Current repository checkpoint

Latest commit inspected:

```text
d61d3f8c911829dbaf37a97f3c18f5700bb6ecea
updating devcontainer.json
```

The GitHub Actions run for that commit was observed as `in_progress` when this checkpoint was written. The previously completed pipeline run was green; the newest run should be treated as pending until GitHub reports its final conclusion.

## Completed

- [x] VS Code Dev Container / Python 3.11
- [x] Dev Container automatically installs `requirements.txt`
- [x] Dev Container joins the local Docker Compose MLflow network
- [x] Dev Container uses `MLFLOW_TRACKING_URI=http://mlflow:5000`
- [x] MLflow artifact volume mounted into the Dev Container for local training
- [x] Reproducible synthetic customer-churn dataset v2
- [x] Logistic Regression with configurable `C`
- [x] 5-fold cross-validation
- [x] Accuracy / Precision / Recall / F1 / ROC-AUC
- [x] MLflow experiment tracking
- [x] Dataset lineage using `dataset_version=v2`
- [x] Deterministic model selection
- [x] MLflow Model Registry
- [x] `customer-churn-model` registration
- [x] Model version 2 created from the selected run
- [x] `production` alias verified against model version 2
- [x] Selected run: `ba05e5087dd848ec844f5d5598d2f2dc`
- [x] Production model verification: version `2`, run `ba05e5087dd848ec844f5d5598d2f2dc`
- [x] FastAPI `/` and `/predict`
- [x] FastAPI `/model-info` lineage endpoint
- [x] Dockerized API
- [x] Docker Compose development stack
- [x] PostgreSQL-backed MLflow metadata
- [x] API tests and model test
- [x] Training-data validation
- [x] Invalid-data negative test
- [x] CI syntax validation
- [x] GitHub Actions quality gate
- [x] CI model registration
- [x] CI model promotion
- [x] CI packaging of the promoted MLflow model
- [x] CI tests against the packaged model
- [x] GHCR image build/push
- [x] Git-SHA image tags
- [x] Kubernetes Deployment + Service
- [x] Readiness/liveness probes
- [x] Resource requests/limits
- [x] Kubernetes inference smoke test
- [x] Flux GitRepository configured against the private GitHub repository
- [x] Flux Kustomization successfully applied the repository revision in Killercoda
- [x] Kubernetes successfully pulled the immutable GHCR image
- [x] Kubernetes API prediction smoke test succeeded
- [x] GitOps manifest commit is marked `[skip ci]` to avoid an unnecessary CI retrigger

## Latest validated model metrics

For the current Dataset v2 / `C=0.1` training run:

```text
Mean CV F1 : 0.6187
CV F1 Std  : 0.0436
Test F1    : 0.6243
Recall     : 0.6211
Precision  : 0.6277
ROC-AUC    : 0.7133
Accuracy   : 0.65
```

The configured quality gate requires:

```text
Mean CV F1 >= 0.60
Test F1    >= 0.60
Recall     >= 0.60
```

The selected candidate passed all three checks.

## Model promotion and packaging

The important new boundary is:

```text
MLflow production alias
        ↓
package_model.py
        ↓
exact promoted model
        ↓
model.pkl
        ↓
model_metadata.json
        ↓
Docker image
```

`src/package_model.py` resolves:

```text
models:/customer-churn-model@production
```

and writes the exact production model to `model.pkl` using `joblib`.

It also records:

```text
model_name
model_version
run_id
dataset_version
```

This means the API image can prove which MLflow model it contains.

## API lineage

`src/api.py` loads the packaged joblib artifact:

```python
joblib.load("model.pkl")
```

and exposes:

```text
GET /model-info
```

The intended response identifies the packaged model version and MLflow run.

Important distinction:

```text
MLflow model
  ≠
model.pkl
  ≠
Docker image
```

They are linked through the packaging step and metadata.

## CI pipeline — current design

```text
Checkout
  ↓
Python 3.11
  ↓
Install dependencies
  ↓
Python syntax validation
  ↓
Training-data validation
  ↓
Training
  ↓
Deterministic model quality gate
  ↓
Register model
  ↓
Promote model to production alias
  ↓
Package exact promoted model
  ↓
pytest
  ↓
GHCR login
  ↓
Build + push immutable Git-SHA image
  ↓
Update Kubernetes manifest
  ↓
Commit desired state with [skip ci]
```

The CI MLflow backend is intentionally ephemeral (`sqlite:///mlflow-ci.db`) for the learning lab. It exists to prove the workflow; the production equivalent would use durable tracking metadata and artifact storage.

## Image and Kubernetes state

The image published by CI uses:

```text
ghcr.io/shaikhtousif1/customer-churn-api:${GITHUB_SHA}
ghcr.io/shaikhtousif1/customer-churn-api:latest
```

The Kubernetes manifest is updated to the immutable Git-SHA image rather than relying on `latest`.

The last Kubernetes image verified in Killercoda was:

```text
ghcr.io/shaikhtousif1/customer-churn-api:17a8e70702449983f6d5f01fc9b537853896c8ff
```

It was successfully pulled and ran in the disposable Kubernetes cluster.

## Flux / GitOps milestone

Flux was installed in Killercoda and reported all four core controllers as Ready:

```text
helm-controller
kustomize-controller
notification-controller
source-controller
```

A private GitHub repository secret was created in the `mlops` namespace and used by a Flux `GitRepository`.

Flux reported:

```text
mlops-production-lab    main@sha1:c757703c    Ready=True
```

The Flux Kustomization then applied the repository revision and created the API Deployment/Service.

The API pod successfully reached `Ready=True`, and the prediction smoke test returned:

```json
{"prediction":1}
```

This proved the basic Git → Flux → Kubernetes reconciliation path.

## Local development networking lesson

The Dev Container initially attempted to reach MLflow at `localhost:5000`, which failed because `localhost` referred to the Dev Container itself.

The final local setup uses the Docker Compose network:

```text
Dev Container
      │
      └── mlops-production-lab_default
                 │
                 └── mlflow:5000
```

The Dev Container now resolves:

```text
mlflow → 172.18.0.3
```

and:

```bash
curl http://mlflow:5000/health
```

returns:

```text
OK
```

The Dev Container also mounts the Compose MLflow artifact volume at `/mlartifacts` so locally trained MLflow models can be logged successfully.

## Important serving decision

The API serves the packaged joblib model rather than pulling directly from MLflow at request time:

```text
MLflow
  ↓
package_model.py
  ↓
model.pkl
  ↓
Docker image
  ↓
FastAPI
```

This is a deliberate teaching architecture. A production platform would normally use durable artifact/object storage and a controlled model deployment mechanism.

## Testing status

The repository has tests for:

```text
API health
API prediction
model loading/prediction
training-data validation
invalid schema/data cases
```

The last locally observed full test result was:

```text
10 passed, 1 warning
```

The warning was a Starlette/httpx deprecation warning and did not fail the tests.

## Known limitation / next validation

Killercoda's disposable session expired after the available session window, so the latest CI-to-Kubernetes model-lineage flow has **not yet been revalidated end-to-end after the final packaging changes**.

This is intentional rather than a failure of the repository state.

The next session should verify:

```text
GitHub Actions
   ↓
GHCR image
   ↓
Flux sees manifest revision
   ↓
Kubernetes rollout
   ↓
GET /model-info
   ↓
model version/run ID matches the model promoted by CI
```

## Next exact milestone

### Milestone: prove model-to-production lineage

Do not add more infrastructure first.

Start a fresh disposable Kubernetes session and verify:

1. Flux controllers are Ready.
2. Flux can authenticate to the private repository.
3. Flux reconciles the latest Git revision.
4. The API pod pulls the immutable GHCR image.
5. `/` returns healthy.
6. `/predict` returns a valid prediction.
7. `/model-info` reports the packaged MLflow model version/run.
8. The reported lineage matches the model promoted during CI.

After that, move to:

```text
Rollback
  ↓
Observability
  ↓
Model/data drift
  ↓
Retraining strategy
  ↓
Production artifact storage
  ↓
AWS/Azure deployment architecture
```

## Project learning objective

The lab is teaching the missing MLOps mental model around the infrastructure skills the learner already has:

```text
ML experiment
→ reproducible training
→ evaluation
→ model selection
→ model registry
→ model promotion
→ model packaging
→ model serving
→ containerization
→ image distribution
→ Kubernetes
→ CI/CD
→ GitOps
→ observability
→ model/data lifecycle
```

The guiding engineering loop remains:

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

## Session-start protocol

At the beginning of the next session:

```text
1. Read PROGRESS.md.
2. Read MLOPS_TEACHING_GUIDE.md.
3. Inspect the current GitHub tree and latest commit.
4. Check the latest CI result.
5. Identify the first unfinished milestone.
6. State the checkpoint briefly.
7. Give only the commands needed for that checkpoint.
```

If repository state contradicts an old chat message, trust the repository.