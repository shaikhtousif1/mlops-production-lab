# MLOps Production Lab

A production-style MLOps learning lab covering reproducible model training, MLflow tracking and registry, model quality gates, model promotion, durable artifact storage, GitHub Actions CI/CD, Hugging Face model releases, GHCR, Kubernetes, and Flux GitOps.

## Current architecture

```text
Dataset
  ↓
Training + CV
  ↓
MLflow tracking
  ├── Supabase PostgreSQL (tracking / registry metadata)
  └── Supabase Storage via S3 API (MLflow artifacts)
  ↓
Quality gate / model selection
  ↓
MLflow Model Registry
  ↓
production alias
  ↓
Package EXACT promoted model
  ↓
Hugging Face release artifact
  ↓
Docker image
  ↓
GHCR
  ↓
GitOps manifest
  ↓
Flux
  ↓
Kubernetes
```

The project intentionally separates these concerns:

```text
MLflow       = model tracking / registry / promotion / artifact metadata
Supabase     = persistent PostgreSQL backend + S3-compatible MLflow artifact storage
HF           = persistent packaged model release artifact for this learning lab
Docker/GHCR  = application runtime artifact
Git          = Kubernetes desired state
Flux         = GitOps reconciliation
Kubernetes   = model-serving runtime
```

## Architecture decisions and why

### 1. Supabase instead of local SQLite for MLflow metadata

The original CI design used an ephemeral SQLite database. Every GitHub Actions runner started with a fresh database, which meant MLflow runs, registered models, and model versions could not reliably persist between CI jobs.

We moved MLflow metadata to Supabase PostgreSQL because it provides a persistent PostgreSQL backend without requiring a separate AWS database account for this learning lab.

```text
MLflow
  ↓
Supabase PostgreSQL
  ├── experiments
  ├── runs
  ├── registered_models
  ├── model_versions
  └── aliases / tags / metrics / params
```

### 2. Supabase Storage instead of local MLflow artifact storage

MLflow metadata and MLflow artifacts are different things. PostgreSQL stores tracking/registry metadata; model files and other MLflow artifacts require an artifact store.

We use Supabase Storage through its S3-compatible API:

```text
MLflow
  ↓
S3 API
  ↓
Supabase Storage bucket: mlflow-artifacts
```

This keeps the artifact layer persistent across GitHub Actions runners while avoiding the need to create an AWS account and S3 bucket for the lab.

### 3. Hugging Face remains a separate release artifact

We deliberately did not replace Hugging Face with MLflow artifact storage.

```text
MLflow artifact store
    = MLflow's run/model artifacts

Hugging Face release
    = immutable packaged model release used by this learning lab
```

The same model can therefore exist in both places for different lifecycle purposes.

### 4. CI and CD are now separated

The previous workflow combined model training, application image creation, and deployment-state updates. We split the deployment stage into a separate workflow.

```text
MLOps CI
  ↓ success
MLOps CD
  ↓
GitOps manifest
  ↓
Flux
  ↓
Kubernetes
```

**CI** is responsible for validation, training, evaluation, registration, promotion, packaging, testing, and image publication.

**CD** is responsible for consuming the successful CI release metadata, updating the Kubernetes desired state, and committing that deployment state to `main`.

The CD workflow checks out `main` rather than the CI SHA so that it can safely commit and push the deployment manifest without a detached-HEAD failure.

The generated deployment commit uses `[skip ci]` to prevent a CI/CD loop.

### 5. Immutable identities are intentionally different

```text
MLflow model version
    = persistent registry version

Model release version
    = packaged release version in Hugging Face

Docker image tag
    = Git SHA identifying the application build
```

These identifiers do not have to be equal. Keeping them separate makes lineage explicit.

## Supabase setup and reuse

The lab uses a Supabase project containing:

```text
PostgreSQL database
Storage bucket: mlflow-artifacts
S3-compatible Storage endpoint
```

### Required GitHub configuration

Store sensitive values as GitHub **Secrets**:

```text
MLFLOW_DATABASE_URI
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
HF_TOKEN
```

Store non-sensitive configuration as GitHub **Variables** where appropriate:

```text
MLFLOW_S3_ENDPOINT_URL
AWS_DEFAULT_REGION
SUPABASE_STORAGE_BUCKET
HF_REPO_ID
```

Do not commit passwords, database connection strings, or Storage secret keys into the repository.

### Connection pattern

The MLflow tracking URI points to the Supabase PostgreSQL connection string. The MLflow artifact store uses the Supabase S3-compatible endpoint.

```text
GitHub Actions
    │
    ├── MLFLOW_TRACKING_URI
    │       ↓
    │   Supabase PostgreSQL
    │
    └── MLFLOW_S3_ENDPOINT_URL + S3 credentials
            ↓
        Supabase Storage
            ↓
        mlflow-artifacts
```

### First-time experiment setup

The repository contains `src/setup_mlflow.py`. Its purpose is to:

1. validate the MLflow PostgreSQL connection;
2. verify that the Supabase Storage bucket exists and is accessible;
3. create the MLflow experiment if it does not exist;
4. ensure the experiment points at the intended persistent artifact location.

The setup step is intended for CI initialization and verification. It should not recreate the database or bucket on every run.

### Important: do not use a local artifact location

The experiment must not point to:

```text
/workspace/mlruns/0
```

or another runner-local path.

The persistent design is:

```text
MLflow experiment
    ↓
S3-compatible artifact location
    ↓
Supabase Storage
```

### Pausing Supabase when finished for the day

For a Free Plan project, Supabase supports manually pausing the project. In the dashboard go to:

```text
Project
  → Settings
  → General
  → Project availability
  → Pause Project
```

Pausing preserves the project data and stops compute usage while paused. Resume the project from the dashboard before running CI again.

A paused project is intentionally unavailable, so MLflow/GitHub Actions cannot connect to it until it is resumed. A paused project may also stop resolving its project hostname while paused.

Do **not** delete the project just to stop it. Deletion is permanent and removes the database and Storage objects.

## Killercoda: Recreate the Kubernetes + Flux Environment

Killercoda sessions are temporary. Use this procedure to recreate the lab from a fresh session.

### Prerequisites

Before starting the Killercoda session, have these ready:

- GitHub username: `shaikhtousif1`
- A GitHub Personal Access Token (PAT) with access to the private repository `shaikhtousif1/mlops-production-lab`
- Access to the Killercoda Kubernetes scenario

**Do not commit or paste the PAT into repository files.** When Git prompts for a password during `git clone`, enter the PAT.

### 1. Clone the private repository

From the Killercoda `controlplane` terminal:

```bash
git clone https://github.com/shaikhtousif1/mlops-production-lab.git
cd mlops-production-lab
```

When prompted:

```text
Username: shaikhtousif1
Password: <YOUR_GITHUB_PAT>
```

Verify the clone:

```bash
git status
git log -1 --oneline
```

### 2. Run the Killercoda bootstrap

Run:

```bash
bash scripts/bootstrap-killercoda.sh
```

The script recreates the Kubernetes/Flux lab, configures Flux to pull this private repository, and reconciles the application deployment.

### 3. Verify Flux

```bash
flux get sources git -n mlops
flux get kustomizations -n mlops
kubectl get pods -n flux-system
```

The Git source and Kustomization should become `READY=True`.

### 4. Verify the application

```bash
kubectl get deployment,pods,svc -n mlops
```

Wait until the API pod is `Running` and `READY 1/1`.

Check the image currently deployed:

```bash
kubectl get deployment customer-churn-api -n mlops \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

### 5. Expose the API locally in Killercoda

The Kubernetes Service is a `ClusterIP`, so `curl http://localhost:8000` will not work until a local port-forward is running.

```bash
kubectl -n mlops port-forward svc/customer-churn-api 8000:8000 >/tmp/customer-churn-api-port-forward.log 2>&1 &
```

Verify it:

```bash
curl http://localhost:8000/
```

Expected:

```json
{"status":"ok"}
```

If it fails:

```bash
cat /tmp/customer-churn-api-port-forward.log
kubectl get pods -n mlops
kubectl describe pod -n mlops -l app=customer-churn-api
```

### 6. Test the API and model lineage

Health:

```bash
curl http://localhost:8000/
```

Model lineage:

```bash
curl http://localhost:8000/model-info
```

Prediction:

```bash
curl -X POST "http://localhost:8000/predict?age=45&tenure_months=24&monthly_charges=80&support_tickets=2&usage_hours=150"
```

To stop the port-forward:

```bash
pkill -f 'kubectl.*port-forward.*customer-churn-api'
```

## GitOps model

```text
GitHub
  |
  | Flux GitRepository
  v
Flux Kustomization
  |
  v
Kubernetes Deployment
  |
  v
GHCR image
  |
  v
customer-churn-api Pod
```

The Kubernetes manifests in Git are the desired state. Do not manually edit the live Deployment as the normal deployment mechanism; changes should flow through Git and Flux.

### GitHub clone authentication vs Flux authentication

There are two separate authentication steps:

1. **Git clone authentication** — used to clone the private repository into Killercoda.
2. **Flux Git authentication** — stored as a Kubernetes Secret so Flux can continuously reconcile the private repository.

The PAT is used during setup but must never be committed to Git.

## Local development

The project supports the VS Code Dev Container and local experimentation.

Typical local workflow:

```bash
python src/train.py --c 0.1
python src/select_model.py
python src/register_model.py
python src/promote_model.py
```

For experimentation, `C` is configurable. The CI candidate is configured in the GitHub Actions workflow.

## Model lifecycle

```text
Train candidate
    ↓
Evaluate
    ↓
Quality gate
    ↓
Register
    ↓
Promote production alias
    ↓
Package exact promoted model
    ↓
Publish immutable learning-lab release to Hugging Face
```

The Hugging Face repository uses:

```text
releases/1/
  model.pkl
  model_metadata.json

releases/2/
  model.pkl
  model_metadata.json
```

`model_metadata.json` records both the persistent release version and the MLflow model version.

## CI/CD flow

The current pipeline is separated into CI and CD workflows.

### MLOps CI

```text
Push to main
   ↓
Validate Python
   ↓
Validate dataset
   ↓
Configure persistent MLflow backend/artifact store
   ↓
Train candidate
   ↓
Model quality gate
   ↓
Register model
   ↓
Promote production alias
   ↓
Package promoted model
   ↓
Publish model release to Hugging Face
   ↓
pytest
   ↓
Build API image
   ↓
Push image to GHCR
```

### MLOps CD

A successful MLOps CI workflow triggers MLOps CD through `workflow_run`.

```text
Successful CI
   ↓
MLOps CD
   ↓
Download release metadata
   ↓
Checkout main
   ↓
Update k8s/deployment.yaml
   ↓
Validate manifest
   ↓
Commit deployment state [skip ci]
   ↓
Push main
   ↓
Flux reconciliation
   ↓
Kubernetes
```

The CD workflow uses the CI commit SHA as the immutable Docker image tag but checks out `main` for its deployment-state commit. This avoids the detached-HEAD push failure encountered during the first CD implementation.

## Current learning milestones

Completed:

- Persistent MLflow PostgreSQL backend
- Persistent S3-compatible MLflow artifact storage
- MLflow model registration and promotion
- Hugging Face packaged release
- GHCR image publication
- Kubernetes serving
- Flux GitOps reconciliation
- Separate CI and CD workflows
- Successful end-to-end CI → CD trigger and deployment-state update

Next:

1. Deliberate model rollback.
2. Deliberate GitOps/application rollback.
3. Observability and model/data drift.
4. Extend toward LLMOps: prompt/version management, evaluation, RAG, vector storage, LLM observability, cost tracking, and guardrails.

## Production-equivalent target architecture

A production platform would normally separate the model lifecycle from application deployment:

```text
Model CI/CD

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
Durable artifact storage
```

and:

```text
Application CI/CD

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

For this lab, Supabase provides a low-cost persistent PostgreSQL + S3-compatible artifact layer. In a production AWS design, the equivalent artifact layer could use S3 with IAM, encryption, lifecycle policies, and durable versioned objects.

## Rollback learning plan

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

This teaches the distinction between **model rollback** and **application rollback**.
