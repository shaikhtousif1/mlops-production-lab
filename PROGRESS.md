# MLOps Production Lab — Progress

## Checkpoint — 2026-10-01

Today's session moved the lab from a basic single-pipeline MLOps demo toward a more production-oriented model lifecycle.

### Current end-to-end concept

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
Persistent model release artifact
  ↓
Docker image
  ↓
GHCR
  ↓
GitOps desired state
  ↓
Flux
  ↓
Kubernetes
```

## Completed / validated

- [x] VS Code Dev Container / Python 3.11
- [x] Local Docker Compose MLflow environment
- [x] MLflow artifact volume mounted into Dev Container
- [x] Reproducible customer-churn dataset v2
- [x] Logistic Regression with configurable `C`
- [x] 5-fold cross-validation
- [x] Accuracy / Precision / Recall / F1 / ROC-AUC
- [x] MLflow experiment tracking
- [x] Dataset lineage using `dataset_version=v2`
- [x] Deterministic model selection
- [x] MLflow Model Registry
- [x] `customer-churn-model` registration
- [x] Model version 2 created locally from selected run
- [x] `production` alias verified locally against model version 2
- [x] FastAPI `/`, `/predict`, and `/model-info`
- [x] Dockerized API
- [x] API tests and model tests
- [x] Training-data validation and negative tests
- [x] GitHub Actions CI
- [x] CI model registration and promotion
- [x] CI packaging of the promoted model
- [x] Hugging Face model repository configured as the learning-lab artifact store
- [x] GHCR image build/push
- [x] Git-SHA image tags
- [x] Kubernetes Deployment + Service
- [x] Kubernetes readiness/liveness probes
- [x] Flux GitRepository + Kustomization
- [x] Private GitHub authentication for Flux
- [x] One-shot/idempotent Killercoda bootstrap
- [x] Kubernetes prediction smoke test
- [x] GitOps manifest updates marked `[skip ci]`

## Important issue found and fixed today

The Hugging Face release discovery code was passing the wrong argument to `HfApi.list_repo_tree()`. The resulting exception was caught and the code incorrectly assumed that no releases existed:

```text
HfApi.list_repo_tree() got an unexpected keyword argument 'path'
```

That caused every CI packaging run to select release `1`.

The code was corrected to use `path_in_repo` and now fails the pipeline if release discovery cannot be performed instead of silently resetting to release 1.

The intended persistent artifact structure is:

```text
releases/1/
  model.pkl
  model_metadata.json

releases/2/
  model.pkl
  model_metadata.json
```

The next CI run must be checked for:

```text
Model release version: 2
Release path: releases/2/
```

## Versioning mental model established

We clarified that these are different identifiers:

```text
MLflow model version
    = version inside a particular MLflow registry/database

Model release version
    = persistent artifact release number in Hugging Face

Docker image tag
    = immutable Git SHA for the application build
```

The CI MLflow backend currently uses:

```text
sqlite:///mlflow-ci.db
```

Therefore each fresh GitHub Actions run has an ephemeral MLflow registry and can start at MLflow model version 1 again. This is acceptable for the learning lab; the persistent release number must come from the artifact repository.

## Production architecture discussion

We discussed that a production environment would normally use durable artifact/object storage such as S3, Azure Blob, or GCS instead of Hugging Face.

Conceptually:

```text
MLflow
  ↓
tracks/registers/promotes model
  ↓
Durable artifact store
  ↓
immutable model artifact
```

S3 is not the model registry itself; it is the durable artifact layer. For this lab we intentionally avoid S3 cost and complexity.

We also established the distinction between:

```text
Model rollback
    production alias v3 → v2

Application/GitOps rollback
    Git commit B → Git commit A → Flux → Kubernetes
```

Both rollback paths will be practiced hands-on.

## Pipeline architecture discussion

The current CI is intentionally a single end-to-end workflow. The production-oriented target is to separate:

### Model CI/CD

```text
Data
 ↓
Training / hyperparameter search
 ↓
Evaluation
 ↓
Quality gate
 ↓
Model registry
 ↓
Promotion
 ↓
Artifact storage
```

### Application CI/CD

```text
Application code
 ↓
Tests
 ↓
Docker build
 ↓
GHCR/ECR/etc.
 ↓
GitOps manifest
 ↓
Flux
 ↓
Kubernetes
```

We will implement this separation after validating the current v2 artifact release.

## Hyperparameter learning note

Changing `C` directly in source code is only being used to demonstrate a new model candidate. It is not the desired production retraining pattern.

The production-style evolution is:

```text
Training trigger
   ↓
Hyperparameter search/configuration
   ↓
Multiple candidates
   ↓
Evaluation
   ↓
Quality gate
   ↓
Select candidate
   ↓
Promote
```

## Current model metrics from Dataset v2 / C=0.1 baseline

```text
Mean CV F1 : 0.6187
CV F1 Std  : 0.0436
Test F1    : 0.6243
Recall     : 0.6211
Precision  : 0.6277
ROC-AUC    : 0.7133
Accuracy   : 0.65
```

Quality gate:

```text
Mean CV F1 >= 0.60
Test F1    >= 0.60
Recall     >= 0.60
```

The baseline candidate passed.

## Killercoda status

The Killercoda session is disposable and has expired/was paused. The repository contains the one-shot bootstrap:

```bash
bash scripts/bootstrap-killercoda.sh
```

The next infrastructure session should start from a fresh Killercoda environment and validate:

```text
clone with PAT
  ↓
bootstrap-killercoda.sh
  ↓
Flux Ready
  ↓
GitRepository Ready
  ↓
Kustomization Ready
  ↓
API Deployment Ready
  ↓
port-forward
  ↓
GET /
GET /model-info
POST /predict
```

The README now explicitly documents the port-forward before the curl commands.

## Next session — exact order

1. Check the latest GitHub Actions run after the Hugging Face release-discovery fix.
2. Confirm `releases/2/` exists in the Hugging Face model repository.
3. Verify `model_metadata.json` for release 2.
4. Recreate Killercoda using the one-shot bootstrap.
5. Verify `/model-info` against the CI-promoted model lineage.
6. Then split Model CI/CD from Application CI/CD.
7. Perform a deliberate model rollback.
8. Perform a deliberate GitOps/application rollback.
9. Add observability and model/data drift.
10. Move toward LLMOps/FDE workflows.

## Project objective

The lab is teaching the production MLOps mental model around the learner's existing DevOps/cloud skills:

```text
ML experiment
→ reproducible training
→ evaluation
→ model selection
→ model registry
→ model promotion
→ model packaging
→ artifact storage
→ model serving
→ containerization
→ image distribution
→ Kubernetes
→ CI/CD
→ GitOps
→ rollback
→ observability
→ model/data lifecycle
→ LLMOps
```

## Session-start protocol

At the beginning of the next session:

```text
1. Read PROGRESS.md.
2. Read MLOPS_TEACHING_GUIDE.md.
3. Inspect the current GitHub tree and latest commit.
4. Check the latest CI result.
5. Verify Hugging Face release state.
6. Identify the first unfinished milestone.
7. State the checkpoint briefly.
8. Give only the commands needed for that checkpoint.
```

If repository state contradicts an old chat message, trust the repository.