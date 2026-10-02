# MLOps Production Lab — Progress

## Checkpoint — 2026-10-02

Today's session moved the lab to a persistent MLflow backend and artifact architecture while keeping the learning environment low-cost and cloud-provider-neutral.

### Current end-to-end concept

```text
Dataset
  ↓
Training + cross-validation
  ↓
MLflow tracking
  ├── Supabase PostgreSQL (persistent metadata)
  └── Supabase Storage via S3 API (MLflow artifacts)
  ↓
Deterministic quality gate / selection
  ↓
MLflow Model Registry
  ↓
Production alias
  ↓
Package EXACT promoted model
  ↓
Persistent Hugging Face release artifact
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
- [x] Reproducible customer-churn dataset v2
- [x] Logistic Regression with configurable `C`
- [x] 5-fold cross-validation
- [x] Accuracy / Precision / Recall / F1 / ROC-AUC
- [x] MLflow experiment tracking
- [x] Dataset lineage using `dataset_version=v2`
- [x] Deterministic model selection
- [x] MLflow Model Registry
- [x] `customer-churn-model` registration
- [x] FastAPI `/`, `/predict`, and `/model-info`
- [x] Dockerized API
- [x] API tests and model tests
- [x] Training-data validation and negative tests
- [x] GitHub Actions CI
- [x] CI model registration and promotion workflow
- [x] CI packaging of the promoted model
- [x] Hugging Face model repository configured as the learning-lab release artifact store
- [x] GHCR image build/push
- [x] Git-SHA image tags
- [x] Kubernetes Deployment + Service
- [x] Kubernetes readiness/liveness probes
- [x] Flux GitRepository + Kustomization
- [x] Private GitHub authentication for Flux
- [x] One-shot/idempotent Killercoda bootstrap
- [x] Kubernetes prediction smoke test
- [x] GitOps manifest updates marked `[skip ci]`
- [x] Supabase PostgreSQL configured as persistent MLflow tracking/registry backend
- [x] Supabase Storage S3-compatible endpoint configured for MLflow artifacts
- [x] `psycopg[binary]` added to dependencies for PostgreSQL connectivity
- [x] `boto3` added to dependencies for S3-compatible MLflow artifact storage
- [x] GitHub Actions updated to use `MLFLOW_DATABASE_URI` and Supabase S3 credentials
- [x] CI workflow updated with a dedicated MLflow experiment setup step

## Persistent MLflow architecture

The previous CI design used an ephemeral SQLite database. This caused every fresh GitHub Actions job to start with a new MLflow registry and could not provide durable model metadata.

The lab now uses:

```text
Supabase PostgreSQL
    ↓
MLflow tracking + Model Registry

Supabase Storage
    ↓
S3-compatible API
    ↓
MLflow model artifacts
```

The GitHub Actions workflow receives these through GitHub Secrets/Variables:

```text
MLFLOW_DATABASE_URI
MLFLOW_S3_ENDPOINT_URL
MLFLOW_S3_REGION
SUPABASE_S3_ACCESS_KEY_ID
SUPABASE_S3_SECRET_ACCESS_KEY
SUPABASE_STORAGE_BUCKET
```

No database password or storage credentials are stored in the repository.

The connection to Supabase PostgreSQL was successfully tested from the Dev Container, and the MLflow schema/tables were created successfully. The `customer-churn-model` registered model and model version 1 were also verified in the persistent database during the migration work.

## Artifact architecture clarification

We explicitly separated two artifact concepts:

```text
MLflow artifact store
    = artifacts generated/managed by MLflow for runs and registered models

Hugging Face release
    = immutable packaged model release used by this learning lab
```

They are complementary, not duplicates serving exactly the same purpose.

For this lab:

```text
Supabase S3
    → MLflow's artifact storage

Hugging Face
    → persistent packaged release consumed by the release workflow
```

In a production AWS environment, S3 could provide the durable MLflow artifact layer without needing Hugging Face for that purpose.

## CI changes completed

The CI workflow now configures the persistent MLflow environment before training:

```text
Configure MLflow experiment + artifact store
        ↓
Run training
        ↓
Quality gate
        ↓
Register model
        ↓
Promote model
        ↓
Package/publish release
        ↓
Tests
        ↓
Build GHCR image
        ↓
Update GitOps manifest
```

All MLflow-related steps use the persistent `MLFLOW_DATABASE_URI`. Training, quality selection, registration, and packaging also receive the S3-compatible artifact-store configuration.

## Current training state

The latest local training run with `C=0.5` produced:

```text
Cross-validation accuracy: 0.65
Cross-validation std:      0.04
Cross-validation F1:       0.62
Cross-validation F1 std:   0.04
Precision:                 0.63
Recall:                    0.62
F1:                        0.62
ROC-AUC:                   0.71
Test accuracy:             0.65
```

The run was successfully written to the persistent MLflow database after the PostgreSQL migration. Model registration was also successfully tested locally:

```text
customer-churn-model
version 1
```

## Important CI issue found during migration

The first CI attempt against Supabase failed because the GitHub runner did not have the PostgreSQL Python driver:

```text
ModuleNotFoundError: No module named 'psycopg'
```

This was fixed by adding:

```text
psycopg[binary]
```

to `requirements.txt`.

The next CI attempt then reached MLflow artifact logging but failed because the MLflow experiment still had a local artifact location:

```text
/workspace/mlruns/0
```

The workflow has now been updated to configure the persistent S3-compatible artifact store before training. The next CI run is the validation checkpoint for that migration.

## Versioning mental model

These identifiers remain intentionally separate:

```text
MLflow model version
    = persistent registry version in Supabase PostgreSQL

Model release version
    = persistent packaged release number in Hugging Face

Docker image tag
    = immutable Git SHA for the application build
```

They do **not** have to be the same.

## Production architecture discussion

A production environment would normally use durable object storage such as S3, Azure Blob, or GCS for MLflow artifacts, with IAM/service identities, encryption, lifecycle management, and appropriate network controls.

For this lab, Supabase provides a low-cost PostgreSQL backend and S3-compatible object storage without requiring a separate AWS account.

## Rollback learning plan

The next hands-on milestone after validating persistent artifacts is rollback.

### Model rollback

```text
production → model v3
             ↓
          rollback
             ↓
production → model v2
```

No retraining is required if v2 remains available as an immutable artifact.

### Application/GitOps rollback

```text
Git commit A → model v2 + image A
Git commit B → model v3 + image B
                    ↓
                 rollback
                    ↓
Git commit A → Flux → Kubernetes
```

This will teach the distinction between **model rollback** and **application rollback**.

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

We will implement this separation after validating the persistent MLflow artifact flow.

## Next session — exact order

1. Run the updated GitHub Actions pipeline and verify MLflow artifacts are written to Supabase Storage.
2. Confirm the MLflow experiment no longer uses `/workspace/mlruns/0` as its artifact location.
3. Verify a CI run and registered model version persist across a separate CI run.
4. Verify the Hugging Face release remains a separate immutable packaged artifact.
5. Validate lineage from CI → MLflow → HF → Docker → Git → Flux → Kubernetes.
6. Split Model CI/CD from Application CI/CD.
7. Perform a deliberate model rollback.
8. Perform a deliberate GitOps/application rollback.
9. Add observability and model/data drift.
10. Extend the platform toward LLMOps/FDE workflows.

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
5. Verify Supabase MLflow artifact state.
6. Verify Hugging Face release state.
7. Identify the first unfinished milestone.
8. State the checkpoint briefly.
9. Give only the commands needed for that checkpoint.
```

If repository state contradicts an old chat message, trust the repository.
