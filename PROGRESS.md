# MLOps Production Lab — Progress

## Checkpoint — 2026-10-02 — End of Day

Today the lab completed the persistent MLflow migration and the separation of CI and CD. Both workflows were successfully triggered and completed after the final CD fix.

### Current end-to-end architecture

```text
Dataset v2
   ↓
Training + cross-validation
   ↓
MLflow tracking
   ├── Supabase PostgreSQL (persistent metadata / registry)
   └── Supabase Storage via S3-compatible API (MLflow artifacts)
   ↓
Quality gate / deterministic selection
   ↓
MLflow Model Registry
   ↓
production alias
   ↓
Package EXACT promoted model
   ↓
Hugging Face persistent release artifact
   ↓
Application image
   ↓
GHCR
   ↓
MLOps CD
   ↓
GitOps manifest
   ↓
Flux
   ↓
Kubernetes
```

## Completed / validated

- [x] VS Code Dev Container / Python 3.11
- [x] Reproducible customer-churn Dataset v2
- [x] Logistic Regression with configurable `C`
- [x] 5-fold cross-validation
- [x] Accuracy / Precision / Recall / F1 / ROC-AUC
- [x] MLflow experiment tracking
- [x] Dataset lineage using `dataset_version=v2`
- [x] Deterministic model selection / quality gate
- [x] MLflow Model Registry
- [x] `customer-churn-model` registration
- [x] Production model alias / promotion
- [x] FastAPI `/`, `/predict`, and `/model-info`
- [x] Dockerized API
- [x] API/model/data validation tests
- [x] GHCR image build and push
- [x] Git-SHA image tags
- [x] Kubernetes Deployment + Service
- [x] Readiness/liveness probes
- [x] Flux GitRepository + Kustomization
- [x] Private GitHub authentication for Flux
- [x] Killercoda bootstrap
- [x] Kubernetes prediction smoke test
- [x] Supabase PostgreSQL as persistent MLflow tracking/registry backend
- [x] Supabase Storage S3-compatible endpoint as MLflow artifact store
- [x] `psycopg[binary]` dependency for PostgreSQL
- [x] `boto3` dependency for S3-compatible artifact access
- [x] GitHub Secrets/Variables configured for MLflow and Supabase Storage
- [x] Dedicated MLflow experiment setup step
- [x] Persistent MLflow experiment verified with artifact location `s3://mlflow-artifacts`
- [x] MLflow `customer-churn-model` and model version persisted in Supabase PostgreSQL
- [x] Hugging Face used as separate packaged model release storage
- [x] MLOps CI workflow separated from MLOps CD
- [x] Successful CI → CD `workflow_run` trigger
- [x] CD successfully updates `k8s/deployment.yaml` and pushes to `main`
- [x] Fixed CD detached-HEAD failure by checking out `main` before committing/pushing
- [x] `[skip ci]` retained on deployment-state commits to avoid CI/CD loops

## Persistent MLflow design decision

### Why we changed from SQLite

The original CI design used an ephemeral SQLite database:

```text
sqlite:///mlflow-ci.db
```

That meant every GitHub Actions runner started with a fresh MLflow database. Runs, registered models, and model versions could not be treated as durable shared state across independent jobs/runs.

We therefore selected Supabase PostgreSQL for the learning lab.

### Why Supabase

The goal was persistent state without introducing an AWS account and S3 setup solely for this lab.

```text
Supabase PostgreSQL
    ↓
MLflow tracking + Model Registry

Supabase Storage
    ↓
S3-compatible API
    ↓
MLflow artifacts
```

This is a learning-lab design choice. Production AWS could use RDS/PostgreSQL plus S3 with IAM, encryption, lifecycle policies, and stronger network controls.

## Supabase configuration model

The repository never stores Supabase passwords or Storage secret keys.

GitHub **Secrets**:

```text
MLFLOW_DATABASE_URI
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
HF_TOKEN
```

GitHub **Variables** / non-sensitive configuration:

```text
MLFLOW_S3_ENDPOINT_URL
AWS_DEFAULT_REGION
SUPABASE_STORAGE_BUCKET
HF_REPO_ID
```

The Storage bucket is:

```text
mlflow-artifacts
```

The S3-compatible endpoint is supplied through `MLFLOW_S3_ENDPOINT_URL`.

### Supabase shutdown procedure

When finished for the day, do not delete the Supabase project. For a Free Plan project, pause it from the Supabase dashboard:

```text
Project
  → Settings
  → General
  → Project availability
  → Pause Project
```

Resume it before running MLflow/CI again. While paused, the MLflow database and Storage API are unavailable, so CI cannot connect until the project is resumed.

## MLflow vs Hugging Face artifact decision

We explicitly separated two concepts:

```text
MLflow artifact store
    = artifacts generated/managed by MLflow for runs and registered models

Hugging Face release
    = immutable packaged model release used by this learning lab
```

They are complementary rather than interchangeable.

The learning lab therefore keeps:

```text
Supabase S3 → MLflow artifacts
Hugging Face → packaged release artifact
```

## CI/CD separation decision

We deliberately separated training/model lifecycle from deployment-state management.

### MLOps CI

```text
Validate
  ↓
Train
  ↓
Quality gate
  ↓
Register
  ↓
Promote
  ↓
Package
  ↓
Publish HF release
  ↓
Test
  ↓
Build/push GHCR image
```

### MLOps CD

```text
Successful MLOps CI
  ↓
workflow_run trigger
  ↓
Download release metadata
  ↓
Checkout main
  ↓
Update k8s/deployment.yaml
  ↓
Validate
  ↓
Commit [skip ci]
  ↓
Push main
  ↓
Flux reconciliation
  ↓
Kubernetes
```

### CD detached-HEAD issue and resolution

The first CD implementation checked out the CI SHA directly. GitHub Actions therefore placed the runner in detached HEAD state. The deployment manifest commit succeeded, but:

```text
fatal: You are not currently on a branch.
```

The workflow was corrected to check out `main` and explicitly push:

```bash
git push origin main
```

After this fix, both MLOps CI and MLOps CD completed successfully.

## Current training checkpoint

The latest local `C=0.5` training run produced:

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

The persistent MLflow database was successfully connected from the Dev Container and MLflow schema tables were created. The `customer-churn-model` registration and model version 1 were verified during the migration work.

## Versioning mental model

Keep these identities separate:

```text
MLflow model version
    = persistent registry version in Supabase PostgreSQL

Model release version
    = persistent packaged release in Hugging Face

Docker image tag
    = immutable Git SHA for the application build
```

They do not have to match.

## Known migration lessons

### PostgreSQL driver

The first CI run against Supabase failed with:

```text
ModuleNotFoundError: No module named 'psycopg'
```

Adding `psycopg[binary]` to `requirements.txt` resolved the database-driver issue.

### Local artifact location

The next migration issue was an existing MLflow experiment pointing at a local path such as:

```text
/workspace/mlruns/0
```

The experiment setup was corrected so the persistent experiment uses the Supabase S3-compatible artifact layer.

### Artifact store and registry are different

A registered model record in PostgreSQL does not itself contain the model file. MLflow needs both persistent metadata and durable artifact storage.

### Secrets are configuration, not code

Database passwords and Storage secret keys belong in GitHub Secrets, never in `train.py`, YAML committed to the repository, or documentation.

## Next session — exact order

1. Read `PROGRESS.md` and `MLOPS_TEACHING_GUIDE.md`.
2. Check the latest repository commit and CI/CD status.
3. Resume Supabase if it was paused.
4. Verify the MLflow experiment and artifact location.
5. Verify the latest Hugging Face release.
6. Verify the latest GitOps deployment and `/model-info` lineage in Kubernetes.
7. Perform a deliberate **model rollback**.
8. Perform a deliberate **GitOps/application rollback**.
9. Add observability and model/data drift.
10. Begin the LLMOps/FDE extension.

Do not spend the next session reworking the CI/CD plumbing unless a new failure requires it. The current CI → CD path has been successfully validated.

## Project objective

The lab is teaching the production MLOps mental model using the learner's existing DevOps/cloud background:

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
5. Check the latest CD result.
6. Verify Supabase MLflow artifact state.
7. Verify Hugging Face release state.
8. Identify the first unfinished milestone.
9. State the checkpoint briefly.
10. Give only the commands needed for that checkpoint.
```

If repository state contradicts an old chat message, trust the repository.
