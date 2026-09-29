# MLOps Production Lab — Hands-on Workbook

This workbook is the executable learning path for the repository. The project is a small customer-churn prediction system, but the real subject is the MLOps lifecycle:

```text
Data → Train → Evaluate → Track → Select → Register → Promote → Package → Publish → Deploy → Reconcile
```

The learner already has strong AWS/Azure, Kubernetes, Docker, Terraform, CI/CD and FluxCD experience. Therefore this workbook focuses on the ML-specific reasoning, model lifecycle, artifact lineage and production delivery boundaries rather than reteaching basic infrastructure.

---

# 0. Current checkpoint

As of 2026-09-29 the lab has reached the **model promotion → packaging → immutable image → GitOps** stage.

Current architecture:

```text
Dataset v2
   ↓
train.py
   ↓
MLflow run
   ↓
select_model.py
   ↓
Quality gate
   ↓
register_model.py
   ↓
MLflow model version
   ↓
promote_model.py
   ↓
production alias
   ↓
package_model.py
   ↓
model.pkl + model_metadata.json
   ↓
Docker image
   ↓
GHCR
   ↓
k8s/deployment.yaml
   ↓
FluxCD
   ↓
Kubernetes
   ↓
FastAPI
```

The next learning task is to prove that the model reported by the running Kubernetes API is the same model that CI promoted.

---

# 1. Prerequisites

You need:

- Git
- VS Code
- VS Code Dev Containers extension
- Docker Desktop with WSL2 integration
- Python 3.11
- `kubectl`
- a disposable Kubernetes cluster
- a GitHub account

Cloud resources are not required. Disposable Kubernetes is sufficient for the current stage.

---

# 2. Repository map

Important paths:

```text
mlops-production-lab/
├── .github/workflows/mlops-ci.yml   # CI pipeline
├── .devcontainer/                   # reproducible local environment
├── data/                             # dataset
├── k8s/                              # Kubernetes desired state
├── mlflow/                           # MLflow server image/config
├── src/
│   ├── generate_data.py
│   ├── validate_data.py
│   ├── train.py
│   ├── select_model.py
│   ├── register_model.py
│   ├── promote_model.py
│   ├── package_model.py
│   ├── predict.py
│   └── api.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── PROGRESS.md
└── MLOPS_TEACHING_GUIDE.md
```

Before changing anything:

```bash
git status
git log -3 --oneline
```

The repository is the source of truth if it differs from an old conversation command.

---

# 3. Reproducible development environment

The Dev Container now joins the Docker Compose network and installs Python dependencies automatically.

Relevant configuration:

```text
network: mlops-production-lab_default
MLFLOW_TRACKING_URI=http://mlflow:5000
/mlartifacts → Compose MLflow artifact volume
postCreateCommand → pip install -r requirements.txt
```

Validate:

```bash
python -c "import pandas, mlflow, sklearn; print('Dependencies OK')"
curl http://mlflow:5000/health
```

Expected:

```text
Dependencies OK
OK
```

Why this matters:

`localhost` inside the Dev Container is the Dev Container itself. Docker Compose service discovery gives us the correct production-like network boundary:

```text
Dev Container → mlflow:5000 → MLflow container
```

---

# 4. Dataset and validation

The project uses reproducible synthetic customer-churn Dataset v2.

Columns:

```text
age
tenure_months
monthly_charges
support_tickets
usage_hours
churned
```

Validate the normal dataset:

```bash
python src/validate_data.py
```

The validator checks schema and value constraints.

The negative-path validation has also been exercised with an invalid age and correctly returned:

```text
VALIDATION FAILED
- Column 'age' contains values outside 0-120
```

This is important because production ML pipelines must fail before training when the input contract is broken.

---

# 5. Train an experiment

Run:

```bash
python src/train.py --c 0.1
```

Training performs:

1. dataset loading
2. train/test split
3. 5-fold cross-validation
4. model training
5. predictions
6. classification metrics
7. ROC-AUC calculation
8. MLflow parameter/metric logging
9. MLflow model logging

The training code records:

```python
mlflow.set_tag("dataset_version", "v2")
```

This gives the model-selection stage dataset lineage.

The current observed `C=0.1` metrics are approximately:

```text
Accuracy   0.65
Mean CV F1 0.6187
CV F1 Std  0.0436
Test F1    0.6243
Recall     0.6211
Precision  0.6277
ROC-AUC    0.7133
```

---

# 6. Model selection and quality gate

Run:

```bash
python src/select_model.py
```

Selection is deterministic:

```text
1. dataset_version=v2
2. complete metric set
3. highest mean CV F1
4. lowest CV F1 standard deviation
5. highest recall
6. highest precision
```

The quality gate currently requires:

```text
Mean CV F1 >= 0.60
Test F1    >= 0.60
Recall     >= 0.60
```

The selected candidate passed all three checks.

Why the test set is not the primary tuning signal:

```text
Training data
   ↓
Cross-validation
   ↓
Model selection
   ↓
Final test evaluation
```

Otherwise the final test set gradually becomes another training/tuning dataset.

---

# 7. Model Registry and promotion

Register the selected model:

```bash
python src/register_model.py
```

Model name:

```text
customer-churn-model
```

The latest manually validated registration created version 2 from run:

```text
ba05e5087dd848ec844f5d5598d2f2dc
```

Promote it:

```bash
python src/promote_model.py
```

Verify:

```bash
python - <<'PY'
from mlflow import MlflowClient
client = MlflowClient()
v = client.get_model_version_by_alias("customer-churn-model", "production")
print("Production version:", v.version)
print("Run ID:", v.run_id)
print("Aliases:", list(v.aliases))
PY
```

The validated result was:

```text
Production version: 2
Run ID: ba05e5087dd848ec844f5d5598d2f2dc
Aliases: ['production']
```

Critical mental model:

```text
MLflow run
   ≠
registered model version
   ≠
production alias
   ≠
Docker image
```

Promotion is the explicit link between registry state and what should be packaged for serving.

---

# 8. Package the promoted model

`src/package_model.py` resolves:

```text
models:/customer-churn-model@production
```

and loads the exact model currently pointed to by the production alias.

It creates:

```text
model.pkl
model_metadata.json
```

`model.pkl` is serialized with `joblib` because `train.py` creates the serving artifact with:

```python
joblib.dump(model, "model.pkl")
```

Therefore the API uses:

```python
joblib.load("model.pkl")
```

Do not use:

```python
mlflow.pyfunc.load_model("model.pkl")
```

because `model.pkl` is not an MLflow model directory.

The metadata file records:

```text
model_name
model_version
run_id
dataset_version
```

This gives the Docker image model lineage.

---

# 9. API and model lineage

The API serves the packaged model:

```text
model.pkl → FastAPI
```

Endpoints:

```text
GET  /
GET  /model-info
POST /predict
```

`/model-info` returns the model lineage embedded by CI.

The important production question is no longer just:

> Is the API healthy?

It is also:

> Which exact model is this API serving?

That is why `/model-info` exists.

---

# 10. Tests

Run:

```bash
pytest -v
```

The latest locally observed suite was:

```text
10 passed, 1 warning
```

The warning was a Starlette/httpx deprecation warning and did not fail the tests.

The test suite covers API behavior, model prediction and data-validation behavior.

The pipeline also compiles the important Python modules before running the workflow.

---

# 11. CI pipeline

The current GitHub Actions workflow is:

```text
Checkout
   ↓
Python 3.11
   ↓
Install requirements
   ↓
py_compile
   ↓
Validate training data
   ↓
Train
   ↓
Quality gate / select
   ↓
Register
   ↓
Promote production alias
   ↓
Package promoted model
   ↓
pytest
   ↓
GHCR login
   ↓
Docker build + push
   ↓
Update Kubernetes image tag
   ↓
Commit desired state with [skip ci]
```

The CI MLflow backend is intentionally ephemeral:

```text
sqlite:///mlflow-ci.db
```

This is sufficient to prove the lifecycle in the learning lab. Production would use durable MLflow metadata and durable artifact storage.

The `[skip ci]` on the generated Kubernetes manifest commit prevents this deployment-state commit from recursively triggering another training/build cycle.

---

# 12. Container image

CI publishes:

```text
ghcr.io/<owner>/customer-churn-api:<git-sha>
ghcr.io/<owner>/customer-churn-api:latest
```

The immutable Git-SHA tag is the deployment reference.

The important lineage is:

```text
Git commit
   ↓
CI run
   ↓
MLflow model version
   ↓
model.pkl
   ↓
Docker image tagged with Git SHA
```

`latest` is retained as a convenience tag but should not be the Kubernetes desired-state reference.

---

# 13. Kubernetes deployment

The deployment uses:

```text
Deployment: customer-churn-api
replicas: 1
containerPort: 8000
```

Probes:

```text
readiness → GET /
liveness  → GET /
```

Resources:

```text
requests: 100m CPU / 128Mi
limits:   500m CPU / 512Mi
```

The current desired-state manifest uses an immutable GHCR Git-SHA image.

The last verified Killercoda image was:

```text
ghcr.io/shaikhtousif1/customer-churn-api:17a8e70702449983f6d5f01fc9b537853896c8ff
```

The image was successfully pulled and the API pod reached Ready.

---

# 14. FluxCD GitOps

Flux has now been introduced.

The disposable Killercoda cluster had these controllers Ready:

```text
helm-controller
kustomize-controller
notification-controller
source-controller
```

A Kubernetes secret was created for the private GitHub repository and referenced by a Flux `GitRepository`.

Flux successfully reported the repository source as Ready and the Kustomization applied the repository revision.

The important flow is:

```text
Git repository
      ↓
Flux GitRepository
      ↓
Flux Kustomization
      ↓
Kubernetes desired state
      ↓
Deployment
      ↓
Pod
```

This is different from CI directly running `kubectl apply`.

CI publishes the artifact and updates desired state.
Flux is responsible for reconciliation.

---

# 15. Why the Kubernetes manifest changes when the image changes

Suppose CI produces:

```text
customer-churn-api:ABC123
```

The GitOps repository records:

```yaml
image: ghcr.io/.../customer-churn-api:ABC123
```

Flux notices the Git change and reconciles Kubernetes.

That gives us an auditable promotion chain:

```text
Model promoted
      ↓
Model packaged
      ↓
Image built
      ↓
Image identified by Git SHA
      ↓
Kubernetes desired state updated
      ↓
Flux reconciles
```

The Git commit is the deployment intent. The immutable image tag is the artifact identity.

---

# 16. Next validation: prove model-to-production lineage

Killercoda's disposable session expired before the final packaging changes could be revalidated end-to-end.

When a new session is available:

### A. Verify Flux

```bash
flux get sources git -n mlops
flux get kustomizations -n mlops
```

### B. Verify workload

```bash
kubectl get deployment,pods,svc -n mlops
kubectl get deployment customer-churn-api -n mlops \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

### C. Verify application

Use the service/port-forward or the available cluster access and test:

```bash
curl http://localhost:8000/
curl -X POST "http://localhost:8000/predict?age=45&tenure_months=24&monthly_charges=80&support_tickets=2&usage_hours=150"
curl http://localhost:8000/model-info
```

### D. Prove lineage

Compare:

```text
CI-promoted MLflow version/run
          ↕
/model-info from Kubernetes
```

The model version and run ID should match.

That is the next definition-of-done checkpoint.

---

# 17. Known failures and lessons

## MLflow artifact failure

A registered model can exist without the serving environment being able to access its artifact.

Lesson:

```text
Registry metadata ≠ artifact availability
```

The lab therefore uses a controlled packaging step rather than making the API depend on live MLflow artifact access.

## Dev Container localhost failure

`localhost:5000` inside the Dev Container was not the MLflow service.

Lesson:

```text
localhost is namespace-local
Docker service DNS is the correct network boundary
```

## `/mlartifacts` permission failure

The mounted volume was initially owned by root, while the Dev Container ran as `vscode`.

After correcting ownership, MLflow successfully logged model artifacts.

Lesson:

```text
A shared Docker volume still needs correct filesystem ownership/permissions.
```

## Wrong model loader

`model.pkl` was initially confused with an MLflow model directory.

Correct:

```python
joblib.load("model.pkl")
```

Lesson: inspect the serialization mechanism before selecting the loader.

## Local Docker image vs Kubernetes runtime

An image on the developer machine is not automatically an image in another Kubernetes runtime.

Lesson:

```text
Build environment
   ≠
Kubernetes runtime
   ≠
Registry
```

GHCR provides the portable distribution boundary.

---

# 18. What not to do yet

Do not add these before completing model-to-production lineage validation:

- AWS EKS
- Azure AKS
- MinIO
- LocalStack
- elaborate secrets infrastructure
- advanced model serving platforms

Those are valid production topics, but they do not solve the current unfinished learning objective.

---

# 19. Next learning milestones

### Milestone 1 — current next task

```text
CI-promoted model
   ↓
GHCR image
   ↓
Flux
   ↓
Kubernetes
   ↓
/model-info
   ↓
prove exact model lineage
```

### Milestone 2

Rollback:

```text
Current image
   ↓
previous Git-SHA image
   ↓
Flux reconciliation
   ↓
verify API
```

### Milestone 3

Observability:

```text
API metrics
Kubernetes metrics
request latency
error rate
prediction volume
```

### Milestone 4

MLOps-specific monitoring:

```text
input drift
prediction drift
model performance
training data quality
```

### Milestone 5

Retraining and promotion:

```text
new data
   ↓
validation
   ↓
training
   ↓
quality gate
   ↓
registry
   ↓
promotion
   ↓
package
   ↓
image
   ↓
GitOps
```

### Milestone 6

Production cloud architecture:

```text
AWS EKS / Azure AKS
+ durable MLflow backend
+ object storage
+ secrets
+ observability
+ rollback
+ governance
```

Cloud comes after the lifecycle is understood in the disposable environment.

---

# 20. Engineering questions

For every new component ask:

1. What problem does it solve?
2. Why was the previous approach insufficient?
3. Where does state live?
4. How is the workload validated?
5. What happens if the process/container/node disappears?
6. How would this change in AWS or Azure?
7. How is it automated?
8. How is it rolled back?
9. How do we prove which model is serving?
10. How do we know the model/data is still behaving correctly?

The objective is not to memorize commands. It is to develop the production MLOps mental model behind the commands.

---

# 21. Session-start protocol

At the beginning of a new session:

```text
1. Read PROGRESS.md.
2. Read this workbook.
3. Inspect the current GitHub tree.
4. Check the latest commit.
5. Check the latest CI result.
6. Identify the first unfinished milestone.
7. State the checkpoint briefly.
8. Give only the commands needed for that checkpoint.
```

Never assume an old chat command is still correct when the repository has changed.