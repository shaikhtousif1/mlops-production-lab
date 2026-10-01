# MLOps Production Lab

A production-style MLOps learning lab covering reproducible model training, MLflow tracking and registry, model quality gates, model promotion, artifact packaging, GitHub Actions CI, Hugging Face model artifacts, GHCR, Kubernetes, and Flux GitOps.

## Current architecture

```text
Dataset
  ↓
Training + CV
  ↓
MLflow tracking
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
MLflow       = model tracking / registry / promotion
HF           = learning-lab model artifact storage
Docker/GHCR  = application runtime artifact
Git          = Kubernetes desired state
Flux         = GitOps reconciliation
Kubernetes   = model-serving runtime
```

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

The project supports the VS Code Dev Container and local Docker Compose MLflow service.

Typical local workflow:

```bash
python src/train.py --c 0.1
python src/select_model.py
python src/register_model.py
python src/promote_model.py
```

For experimentation, `C` is configurable. The current CI candidate is intentionally configured separately in the GitHub Actions workflow.

## Model lifecycle

The model pipeline currently demonstrates:

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

`model_metadata.json` records both the persistent release version and the CI-local MLflow model version. The CI MLflow database is intentionally ephemeral, so MLflow model version numbers restart across fresh CI jobs; the Hugging Face release number is the persistent artifact version.

### Important artifact-version distinction

```text
MLflow version
    = registry version inside the MLflow environment

Model release version
    = persistent artifact release stored in Hugging Face

Docker image tag
    = immutable Git SHA identifying the application build
```

These numbers do **not** have to be the same.

## CI/CD flow

The current learning pipeline is still a single end-to-end GitHub Actions workflow:

```text
Push to main
   ↓
Validate Python
   ↓
Validate dataset
   ↓
Train candidate
   ↓
Model quality gate
   ↓
Register
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
   ↓
Update Kubernetes desired state
   ↓
Flux reconciles Kubernetes
```

The current CI training candidate uses `C=0.5` to demonstrate a new model candidate. This is a teaching mechanism, not the intended production approach. The eventual design should make hyperparameter search/configuration explicit rather than requiring source-code edits for every experiment.

## Production-equivalent architecture we will learn next

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
Artifact storage
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

For the lab, Hugging Face is used instead of S3 to avoid unnecessary cloud cost. In a production AWS design, the artifact layer could use S3 with IAM, encryption, lifecycle policies, and durable versioned objects.

## Rollback learning plan

The next hands-on milestone is rollback. We will deliberately create multiple model/application releases and practice both:

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

## Next learning milestones

1. Verify persistent Hugging Face `releases/2/` after the corrected release-discovery code.
2. Validate model lineage from CI → HF → Docker → Git → Flux → Kubernetes.
3. Split model CI/CD and application CI/CD conceptually and then implement the separation.
4. Perform a model rollback.
5. Perform a GitOps/application rollback.
6. Add observability and model/data drift.
7. Introduce a production-style durable artifact store concept using S3/Azure Blob/GCS without unnecessary cloud spend.
8. Extend the platform toward LLMOps: prompt/version management, evaluation, RAG, vector storage, LLM observability, cost tracking, and guardrails.
