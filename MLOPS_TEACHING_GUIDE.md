# MLOps Production Lab — Teaching Guide

This guide explains the same learning path used in `mlops-production-lab`, but is written so another engineer can teach or follow it without needing the original conversation.

The goal is **not** to teach isolated tools. The goal is to show how an ML workload moves from experimentation to a repeatable production system.

---

# 1. What are we building?

We are building a small customer-churn prediction platform.

The model predicts whether a customer is likely to churn from:

- age
- tenure in months
- monthly charges
- support tickets
- usage hours

The project deliberately evolves through multiple stages:

```text
Dataset
   ↓
Training
   ↓
Evaluation
   ↓
Experiment tracking
   ↓
Model selection
   ↓
Model Registry
   ↓
Prediction API
   ↓
Docker
   ↓
Docker Compose
   ↓
Kubernetes
   ↓
CI/CD + GitOps
   ↓
Monitoring + retraining
```

The important lesson is the **system lifecycle**, not the churn model itself.

---

# 2. Start with a deliberately imperfect dataset

The first version used only 20 synthetic records. Several Logistic Regression configurations produced nearly perfect results.

That creates a bad teaching example because the model-selection problem disappears.

We therefore generated Dataset v2 with 1,000 records and more realistic overlap/noise.

Run:

```bash
python src/generate_data.py
```

Expected characteristics:

```text
1,000 records
~47.6% churn
```

The generator uses a fixed seed so the dataset is reproducible.

## Teaching point

A machine-learning pipeline is only as useful as the experimental conditions around it. A tiny, overly easy dataset can hide problems in model comparison.

---

# 3. Train the first model

We use Logistic Regression because it is simple enough to understand while still exposing the important MLOps concepts.

Example:

```bash
python src/train.py --c 0.1
```

The training code performs:

1. Load dataset
2. Separate features and target
3. Stratified train/test split
4. 5-fold cross-validation
5. Model training
6. Prediction
7. Metric calculation
8. MLflow logging
9. Model artifact logging

---

# 4. Understand the metrics

The project records:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- Mean CV accuracy
- CV accuracy standard deviation
- Mean CV F1
- CV F1 standard deviation

There is an important distinction between predictions and probabilities.

```python
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]
```

Use `predictions` for classification metrics such as F1.

Use `probabilities` for ROC-AUC.

## Teaching point

Do not treat all metrics as interchangeable. Each metric answers a different question.

---

# 5. Why cross-validation matters

Instead of evaluating a model on one arbitrary training split, we use 5-fold cross-validation.

Conceptually:

```text
Dataset
   ↓
┌────┬────┬────┬────┬────┐
│ F1 │ F1 │ F1 │ F1 │ F1 │
└────┴────┴────┴────┴────┘
          ↓
      Mean CV F1
          +
       CV Std
```

The mean tells us typical performance across folds.

The standard deviation gives a basic view of stability across folds.

---

# 6. Why MLflow exists

Without experiment tracking, an engineer quickly ends up with:

```text
model_final.py
model_final2.py
model_final_new.py
model_final_really_final.py
```

MLflow gives us a structured record of experiments.

A run contains things such as:

```text
Run
 ├── Parameters
 ├── Metrics
 ├── Tags
 └── Artifacts
```

For this project, parameters include:

```text
C
max_iter
test_size
random_state
```

Metrics include:

```text
accuracy
precision
recall
f1
roc_auc
mean_f1
std_f1
```

---

# 7. Critical concept: an MLflow run is NOT a container

This confused us initially, so it is worth teaching explicitly.

An MLflow run represents **one experiment execution**.

A container is a **runtime environment**.

One container can execute many MLflow runs:

```text
Dev Container
    │
    ├── Run C=0.01
    ├── Run C=0.1
    ├── Run C=1
    ├── Run C=10
    └── Run C=100
```

Think:

```text
Container = where the code runs
MLflow run = what happened during one experiment
```

This distinction becomes extremely important when designing MLOps platforms.

---

# 8. Dataset lineage is part of experiment lineage

The project initially had old MLflow runs from Dataset v1.

When Dataset v2 was generated, the old runs were still visible.

Without a dataset-version filter, the selector found an old perfect-looking run and selected it.

We therefore added:

```python
mlflow.set_tag("dataset_version", "v2")
```

The selector now filters on that tag.

## Teaching point

Never blindly compare models trained on different data versions.

A model result should be traceable to:

```text
Dataset version
      ↓
Code version
      ↓
Parameters
      ↓
Training run
      ↓
Model artifact
```

This is model lineage.

---

# 9. Hyperparameter experimentation

We tested:

```text
C = 0.01
C = 0.1
C = 1
C = 10
C = 100
```

The approximate CV-F1 results were:

| C | Mean CV F1 | CV F1 Std |
|---:|---:|---:|
| 0.01 | 61.61% | 4.54% |
| 0.1 | 61.87% | 4.36% |
| 1 | 61.57% | 3.96% |
| 10 | 61.57% | 3.96% |
| 100 | 61.57% | 3.96% |

C=0.1 is numerically highest, but the difference is tiny.

That is an important lesson:

> A metric winner is not automatically a practically meaningful winner.

The system still needs a deterministic selection policy, but we should not exaggerate a 0.26 percentage-point difference.

---

# 10. Model selection policy

The project contains:

```text
src/select_model.py
```

The selector follows this policy:

```text
1. Filter dataset_version=v2
2. Remove incomplete runs
3. Highest mean CV F1
4. Lowest CV F1 standard deviation
5. Highest recall
6. Highest precision
```

The selected candidate was:

```text
C = 0.1
Mean CV F1 = 0.6187
CV F1 Std = 0.0436
Test F1 = 0.6243
Recall = 0.6211
Precision = 0.6277
```

## Why not select on test F1?

Because repeatedly using the final test set for model decisions turns it into a tuning dataset.

Instead:

```text
Training data
      ↓
Cross-validation
      ↓
Model selection
      ↓
Final test evaluation
```

The test set should remain as an independent final check as much as possible.

---

# 11. ML Engineer vs MLOps Engineer

This project intentionally crosses both areas so the boundary becomes clear.

## ML Engineer / Data Scientist responsibilities

Typically include:

- feature engineering
- model architecture
- hyperparameter tuning
- evaluation methodology
- business metrics
- model-quality requirements

## MLOps responsibilities

Typically include:

- reproducible training
- experiment tracking infrastructure
- model registry
- model packaging
- serving
- CI/CD
- infrastructure
- Kubernetes
- cloud integration
- observability
- drift detection
- retraining automation
- promotion and rollback

The MLOps engineer does not need to become the world's best statistician. They need enough ML understanding to build reliable systems around ML workloads.

---

# 12. Model Registry

After selecting the candidate, we introduced the MLflow Model Registry.

The model was registered as:

```text
customer-churn-model
Version 1
```

This changes the mental model from:

```text
some model artifact on disk
```

to:

```text
named model
   ↓
version
   ↓
controlled lifecycle
```

That is the beginning of model deployment governance.

---

# 13. Prediction service

A prediction script loads the registered model:

```text
models:/customer-churn-model/1
```

Then we created a FastAPI service.

Endpoints:

```text
GET  /
POST /predict
```

The service receives customer attributes and returns:

```json
{"prediction": 1}
```

Swagger/OpenAPI makes this particularly useful for learning because the API can be tested interactively from the browser.

---

# 14. Why environment variables matter

The API does not hardcode the MLflow server address anymore.

It reads:

```text
MLFLOW_TRACKING_URI
MODEL_URI
```

This is important because the same image should be usable in different environments.

For example:

```text
Local
  → http://mlflow:5000

Kubernetes
  → http://mlflow.namespace.svc:5000

Cloud
  → managed/external MLflow endpoint
```

The image should not need to be rebuilt just because the environment changed.

---

# 15. Dockerfile vs Docker Compose

This is another critical distinction.

## Dockerfile

Defines how to build **one image**.

```text
Dockerfile
    ↓
API image
```

## Docker Compose

Defines how **multiple services work together**.

```text
Compose
 ├── PostgreSQL
 ├── MLflow
 └── FastAPI
```

In other words:

```text
Dockerfile = packaging
Compose    = local orchestration
```

Compose is not Kubernetes. But the mental model is useful preparation for Kubernetes.

---

# 16. Current Compose architecture

The project now uses:

```text
                    Docker Compose
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   PostgreSQL          MLflow          FastAPI
     :5432              :5000            :8000
        │                │                │
        │                ├── Tracking     │
        │                ├── Registry     │
        │                └── Artifacts    │
        │                                 │
        └─────────────────────────────────┘
```

### PostgreSQL

Stores MLflow backend metadata and model-registry information.

### MLflow

Provides:

- tracking server
- experiment UI
- model registry

### FastAPI

Provides model inference.

### Persistent volumes

```text
postgres_data
mlflow_artifacts
```

These survive container replacement.

---

# 17. Why PostgreSQL replaced local SQLite

The original development environment used local SQLite/file-based MLflow state.

That is useful for a single developer learning MLflow.

For a shared service, a database-backed tracking server is a better architecture.

The conceptual split is:

```text
PostgreSQL
   ↓
experiments
runs
parameters
metrics
registry metadata

Artifact storage
   ↓
model files
plots
other artifacts
```

This distinction becomes even more important when the artifact backend moves to S3.

---

# 18. The S3 lesson

We initially tried to add MinIO and LocalStack as local S3-compatible storage.

The current environment introduced image/registry/licensing friction, so we deliberately removed that complexity rather than allowing the tutorial to become a MinIO/LocalStack troubleshooting session.

The architectural target remains:

```text
Local learning
     ↓
Docker volume

Production
     ↓
Object storage
     ↓
AWS S3
```

The MLflow image already includes `boto3` in preparation for that future step.

---

# 19. Compose troubleshooting lessons

A successful command such as:

```bash
docker compose up -d
```

does not prove the whole application is healthy.

Always check:

```bash
docker compose ps -a
```

If a service exited:

```bash
docker compose logs <service>
```

Examples:

```bash
docker compose logs mlflow
docker compose logs api
```

This is an important production mindset:

> Container creation is not the same thing as application health.

---

# 20. What should be productionized next?

The current stack is intentionally not the final production platform.

Next improvements should be:

### Model lifecycle

- dynamic model version selection
- promotion strategy
- rollback strategy

### Artifact storage

Move from local Docker volume to S3.

### Secrets

Remove plain-text database credentials from Compose and introduce proper secret management.

### CI

Automate:

```text
Git push
   ↓
Tests
   ↓
Train / validate
   ↓
Build image
   ↓
Push image
```

### Kubernetes

Deploy:

```text
FastAPI
MLflow
PostgreSQL / managed DB
```

using Kubernetes primitives.

### GitOps

Move deployment configuration into Git and use a GitOps controller to reconcile the desired state.

### Observability

Monitor:

- API latency
- request rate
- errors
- model prediction distribution
- resource usage
- model/data drift

### Retraining

Eventually:

```text
New data
   ↓
Training
   ↓
Evaluation
   ↓
Model selection
   ↓
Registry
   ↓
Promotion
   ↓
Deployment
```

---

# 21. Recommended teaching sequence

If teaching this project to another engineer, do not dump all tools on them at once.

Use this sequence:

```text
Session 1
ML basics + dataset + training

Session 2
Evaluation + cross-validation + MLflow

Session 3
Experiment comparison + model selection

Session 4
Model Registry + prediction

Session 5
FastAPI + Swagger

Session 6
Docker

Session 7
Docker Compose + PostgreSQL + MLflow

Session 8
CI/CD

Session 9
Kubernetes

Session 10
GitOps + monitoring + retraining
```

At every stage ask:

1. What problem are we solving?
2. Why does the previous approach stop being sufficient?
3. What does the new tool provide?
4. Where does state live?
5. How do we validate it?
6. What would change in production?

That keeps the training architecture-driven rather than command-driven.

---

# 22. The key mental model

The most important takeaway is this:

```text
ML Engineer creates a model.

MLOps Engineer creates the system that makes the model
reproducible, deployable, observable, governable and replaceable.
```

A model is an artifact.

The MLOps platform is the system around that artifact.

The project is now transitioning from learning the artifact to engineering that system.
