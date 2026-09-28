# MLOps Production Lab — Hands-on Workbook

This workbook is the executable version of the lab. Another engineer should be able to clone the repository, follow the checkpoints, validate each result, and understand **why** each step exists.

The project is a small customer-churn prediction system, but the real subject is the MLOps lifecycle:

```text
Data → Train → Evaluate → Track → Select → Register → Test → Package → Publish → Deploy → Automate
```

---

# 0. Prerequisites

You need:

- Git
- VS Code
- VS Code Dev Containers extension
- Docker Desktop with WSL2 integration
- Python 3.11 if running outside the Dev Container
- `kubectl` for Kubernetes practice
- a Kubernetes cluster you can dispose of after the exercise
- a GitHub account

Cloud resources are **not required** for this workbook.

The lab intentionally uses disposable Kubernetes environments so the learner can practice deployment without maintaining AWS EKS or Azure AKS.

---

# 1. Clone and open the project

```bash
git clone https://github.com/shaikhtousif1/mlops-production-lab.git
cd mlops-production-lab
```

Open the folder in VS Code and reopen it in the Dev Container.

Verify:

```bash
python --version
git --version
```

Expected Python:

```text
Python 3.11.x
```

---

# 2. Understand the repository

Important paths:

```text
mlops-production-lab/
├── .github/workflows/mlops-ci.yml   # CI pipeline
├── data/                             # datasets
├── k8s/                              # Kubernetes manifests
├── mlflow/                           # MLflow server image
├── src/
│   ├── generate_data.py              # dataset generator
│   ├── train.py                      # training + MLflow logging
│   ├── select_model.py               # model quality gate
│   ├── register_model.py             # registry
│   ├── predict.py                    # prediction script
│   └── api.py                        # FastAPI serving
├── tests/
│   ├── test_api.py
│   └── test_model.py
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── PROGRESS.md
```

Before doing anything else:

```bash
git status
```

The working tree should normally be clean.

---

# 3. Generate the dataset

Run:

```bash
python src/generate_data.py
```

The generator uses a fixed seed so the dataset is reproducible.

Inspect it:

```bash
head data/customers.csv
```

The dataset contains:

```text
age
tenure_months
monthly_charges
support_tickets
usage_hours
churned
```

Why synthetic data?

Because the goal is to learn the engineering lifecycle without requiring a real customer dataset.

Why not use the original tiny dataset?

The original 20-row dataset made several configurations look almost perfect, which removed the interesting model-selection problem. Dataset v2 introduces enough overlap/noise to make evaluation imperfect and therefore useful.

---

# 4. Train one experiment

Run:

```bash
python src/train.py --c 0.1
```

The training workflow performs:

1. dataset loading
2. train/test split
3. 5-fold cross-validation
4. model training
5. prediction
6. metric calculation
7. MLflow parameter/metric logging
8. MLflow model logging

Key distinction:

```python
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]
```

Use hard predictions for classification metrics. Use probabilities for ROC-AUC.

---

# 5. Run multiple experiments

The important parameter is Logistic Regression `C`.

Run:

```bash
python src/train.py --c 0.01
python src/train.py --c 0.1
python src/train.py --c 1
python src/train.py --c 10
python src/train.py --c 100
```

The point is not to memorize Logistic Regression. The point is to create multiple reproducible experiments that can be compared.

The project records the dataset version as an MLflow tag:

```python
mlflow.set_tag("dataset_version", "v2")
```

This prevents old Dataset v1 runs from being accidentally selected.

---

# 6. Understand model selection

Run:

```bash
python src/select_model.py
```

The selector applies a deterministic policy:

```text
1. dataset_version=v2
2. complete runs only
3. highest mean CV F1
4. lowest CV F1 standard deviation
5. highest recall
6. highest precision
```

Why not repeatedly select using test F1?

Because the final test set can become an implicit tuning dataset.

The intended flow is:

```text
Training data
   ↓
Cross-validation
   ↓
Model selection
   ↓
Final test evaluation
```

---

# 7. Understand MLflow Model Registry

Register the selected model:

```bash
python src/register_model.py
```

The project uses the registered model name:

```text
customer-churn-model
```

The working checkpoint has version 1 with the `production` alias.

You can inspect it through the MLflow UI when the Compose stack is running, or with the MLflow client.

Important mental model:

```text
Experiment run
    ≠
Model version
    ≠
Docker image
```

They are related, but they solve different problems.

---

# 8. Run the local API

The API currently packages `model.pkl` directly into the container image.

This is deliberate because the local MLflow artifact-storage path proved unnecessarily distracting for this learning objective.

The model is created by training with:

```python
joblib.dump(model, "model.pkl")
```

and served with:

```python
joblib.load("model.pkl")
```

Do not use:

```python
mlflow.pyfunc.load_model("model.pkl")
```

because `model.pkl` is a joblib artifact, not an MLflow model directory.

---

# 9. Run API tests

Run the complete test suite:

```bash
pytest -v
```

Expected:

```text
3 passed
```

The tests cover:

```text
GET /
POST /predict
model.pkl loading + prediction
```

If you see:

```text
ModuleNotFoundError: No module named 'src'
```

make sure `pytest.ini` contains:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Then rerun:

```bash
pytest -v
```

---

# 10. Run the API with Docker Compose

Start the stack:

```bash
docker compose up -d
```

Check service health:

```bash
docker compose ps -a
```

If anything is not running:

```bash
docker compose logs <service>
```

The Compose architecture is:

```text
PostgreSQL
    ↓
MLflow
    ↓
FastAPI
```

Check the API:

```bash
curl http://localhost:8000/
```

Expected:

```json
{"status":"ok"}
```

Run prediction:

```bash
curl -X POST "http://localhost:8000/predict?age=45&tenure_months=24&monthly_charges=80&support_tickets=2&usage_hours=150"
```

Expected shape:

```json
{"prediction":1}
```

The exact prediction is model/data dependent; the important contract is that the endpoint returns a valid class.

---

# 11. Build the production-style API image

```bash
docker compose build api
```

The root Dockerfile does the important packaging work:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY model.pkl .
COPY src ./src
```

The resulting image contains everything required to run the API.

This is the first important production-style boundary:

```text
Developer workspace
       ↓
Portable container image
```

---

# 12. Publish the image to GHCR

The GitHub Actions workflow publishes:

```text
ghcr.io/<owner>/customer-churn-api:<git-sha>
ghcr.io/<owner>/customer-churn-api:latest
```

The package must be readable by the Kubernetes environment. For a disposable public-learning environment, making the GHCR package public is the simplest option.

Verify from another environment:

```bash
docker pull ghcr.io/<owner>/customer-churn-api:latest
```

If the pull works without credentials, the package is public/readable.

---

# 13. Prepare Kubernetes

Use a disposable Kubernetes cluster.

Verify access:

```bash
kubectl config get-contexts
kubectl get nodes
```

You need at least one node in `Ready` state.

Do not create AWS EKS or Azure AKS just for this workbook. The objective here is Kubernetes deployment mechanics.

---

# 14. Deploy the API

Inspect the manifests:

```bash
cat k8s/deployment.yaml
cat k8s/service.yaml
```

Apply them:

```bash
kubectl apply -f k8s/
```

Check:

```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

Wait until:

```text
customer-churn-api   1/1
```

If the pod is stuck:

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

---

# 15. Understand the local-image trap

On Docker Desktop Kubernetes, an image built in Docker Desktop may not automatically be available to Kubernetes depending on the runtime configuration.

A common disposable-lab symptom is:

```text
ErrImageNeverPull
```

If using:

```yaml
imagePullPolicy: Never
```

Kubernetes expects the image to already exist in its container runtime.

For the disposable online cluster, avoid this problem by pulling the GHCR image directly.

This is a useful lesson:

```text
Docker image on my laptop
        ≠
Docker image available to Kubernetes
```

A registry creates the distribution boundary.

---

# 16. Validate the Kubernetes service

Port-forward:

```bash
kubectl port-forward service/customer-churn-api 8001:8000
```

In another terminal:

```bash
curl http://localhost:8001/
```

Expected:

```json
{"status":"ok"}
```

Then:

```bash
curl -X POST "http://localhost:8001/predict?age=45&tenure_months=24&monthly_charges=80&support_tickets=2&usage_hours=150"
```

Expected shape:

```json
{"prediction":1}
```

At this point you have proven:

```text
GHCR
  ↓
Kubernetes
  ↓
Pod
  ↓
FastAPI
  ↓
Model
  ↓
Prediction
```

---

# 17. Understand the current CI pipeline

Open:

```text
.github/workflows/mlops-ci.yml
```

The current pipeline is:

```text
Checkout
  ↓
Python setup
  ↓
Install dependencies
  ↓
Syntax validation
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

The pipeline already tests the application before publishing the image.

That is the current CI boundary.

---

# 18. What we deliberately skip

Do not spend time implementing these before the next milestone:

- AWS EKS
- Azure AKS
- MinIO
- LocalStack
- production secrets management
- elaborate local artifact-storage infrastructure

Those are real production topics, but they do not need to block the current learning objective.

The disposable Kubernetes environment is enough.

---

# 19. Next hands-on milestone: CI-driven deployment

The next exercise is to extend the existing pipeline from:

```text
Build → Push
```

to:

```text
Build
  ↓
Push GHCR
  ↓
Deploy Kubernetes
  ↓
Wait for rollout
  ↓
Run smoke test
```

The first version should deploy the immutable Git-SHA image, not `latest`.

Target flow:

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
kubectl set image / manifest update
   ↓
rollout status
   ↓
API smoke test
```

Only after this works should GitOps be introduced.

---

# 20. GitOps milestone

After CI-driven deployment works, move deployment responsibility into Git:

```text
Application repository
        ↓
Deployment configuration
        ↓
FluxCD
        ↓
Kubernetes
```

The key lesson will be the difference between:

```text
CI = build / test / publish
CD = deploy
GitOps = desired state stored in Git + reconciliation
```

---

# 21. Production evolution

The final learning path is:

```text
Python training
      ↓
MLflow
      ↓
Model Registry
      ↓
FastAPI
      ↓
Docker
      ↓
GHCR
      ↓
Kubernetes
      ↓
CI/CD
      ↓
FluxCD
      ↓
Observability
      ↓
Drift detection
      ↓
Retraining
      ↓
Promotion / rollback
      ↓
AWS EKS / Azure AKS
```

The cloud comes last because the same deployment concepts can be learned without paying for infrastructure.

---

# 22. Troubleshooting cheat sheet

### `ModuleNotFoundError: No module named 'src'`

Run from repository root and ensure `pytest.ini` contains:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

### `Could not find an MLmodel configuration file`

You tried to load a joblib `.pkl` file with MLflow PyFunc. Use:

```python
joblib.load("model.pkl")
```

### `STACK_GLOBAL requires str`

Same root cause: the file is joblib/pickle data and should be loaded with joblib.

### API container exits

```bash
docker compose logs api --tail=50
```

### Kubernetes `ErrImageNeverPull`

The Kubernetes runtime does not have the local image. Push/pull through a registry or import the image into the correct runtime.

### Kubernetes pod pending

```bash
kubectl describe pod <pod-name>
```

### Kubernetes API test

```bash
kubectl port-forward service/customer-churn-api 8001:8000
curl http://localhost:8001/
```

---

# 23. Definition of done for the current phase

You are finished with the current phase when all of these are true:

```text
[x] pytest -v → 3 passed
[x] API runs in Docker
[x] image exists in GHCR
[x] Kubernetes pod is Running
[x] readiness/liveness probes pass
[x] / returns 200
[x] /predict returns a valid prediction
[x] CI builds and publishes the image
```

Then stop adding infrastructure.

The next task is CI-driven Kubernetes deployment.

---

# 24. Engineering questions to ask at every step

For every tool introduced, answer:

1. What problem does it solve?
2. Why was the previous approach insufficient?
3. Where does state live?
4. How is the workload validated?
5. What happens when the process/container/node disappears?
6. How would this change in AWS or Azure?
7. How would this be automated?
8. How would we roll it back?

That is the core of the workbook: **do the task, understand the failure mode, then connect it to the production equivalent.**
