# MLOps Production Lab — Progress

## Current checkpoint — 2026-09-23

### Environment
- GitHub repo: shaikhtousif1/mlops-production-lab
- Active development environment: VS Code Dev Container
- Base image: Python 3.11
- Docker Desktop + WSL2 integration working
- MLflow: 3.16.1

### ML project
- Project: Customer churn prediction
- Dataset: 20 synthetic customer records
- Training split: 16 samples
- Test split: 4 samples
- Model: scikit-learn Logistic Regression
- Current accuracy: 1.00 (not production evidence; dataset is intentionally tiny/simple)

### MLOps concepts completed
- ML lifecycle basics: data → features/target → train/test split → model → prediction → metric
- Experiment tracking with MLflow
- Logged parameters: model_type, max_iter, test_size, random_state
- Logged metric: accuracy
- Logged trained model artifact with mlflow.sklearn.log_model()
- Understood distinction:
  - Experiment/run = what happened during a training execution
  - Model artifact = trained model produced by a run
  - Model Registry = managed/versioned lifecycle for selected models
  - Run IDs and model versions are not the same thing
- Understood that an older run (for example Run #34) can be registered later; registration does not require the latest run.

### Next learning steps
1. Run multiple experiments with a tunable hyperparameter (for example Logistic Regression C).
2. Compare runs in MLflow.
3. Register a selected model in the Model Registry.
4. Learn model versioning and lifecycle/promotion.
5. Build model serving API.
6. Dockerize serving.
7. Add CI/CD.
8. Deploy to Kubernetes.
9. Add model/inference monitoring and drift.
10. Add retraining workflow.

## Working principle
Learn by problem → pain → tool → implementation. Keep GitHub as the source of truth so the project can be resumed from another machine.
