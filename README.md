# MLOps Production Lab

A production-style MLOps learning lab covering model training, MLflow tracking and registry, model quality gates, containerization, GitHub Actions CI, GHCR, Kubernetes, and Flux GitOps.

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

Run the repository bootstrap script:

```bash
bash scripts/bootstrap-killercoda.sh
```

The script recreates the Kubernetes/Flux lab, configures Flux to pull this private repository, and reconciles the application deployment.

If the script asks for the GitHub PAT, provide the same PAT used for the repository clone.

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

The Kubernetes Service is a `ClusterIP`, so `curl http://localhost:8000` will not work until we create a local port-forward.

Run the port-forward in the background:

```bash
kubectl -n mlops port-forward svc/customer-churn-api 8000:8000 >/tmp/customer-churn-api-port-forward.log 2>&1 &
```

Verify the port-forward is active:

```bash
curl http://localhost:8000/
```

If needed, inspect the port-forward log:

```bash
cat /tmp/customer-churn-api-port-forward.log
```

### 6. Test the API

Health/root endpoint:

```bash
curl "http://localhost:8000/"
```

Prediction test:

```bash
curl -X POST "http://localhost:8000/predict?age=45&tenure_months=24&monthly_charges=80&support_tickets=2&usage_hours=150"
```

Expected response format:

```json
{"prediction":1}
```

To stop the port-forward later:

```bash
pkill -f 'kubectl.*port-forward.*customer-churn-api'
```

### GitOps model

The intended deployment flow is:

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

### Important: GitHub clone authentication vs Flux authentication

There are two separate authentication steps:

1. **Git clone authentication** - used by you to clone the private repository into the Killercoda VM.
2. **Flux Git authentication** - stored as a Kubernetes Secret so Flux can continuously reconcile the private repository after the bootstrap finishes.

The PAT is therefore used during setup, but it should never be committed to Git.

## Local development

The project also supports the VS Code Dev Container. The development container is configured to reach the local MLflow service when the Docker Compose network is available.

Typical local workflow:

```bash
python -c "import pandas, mlflow, sklearn; print('Dependencies OK')"
python src/train.py --c 0.1
python src/select_model.py
python src/register_model.py
python src/promote_model.py
```

MLflow tracking is provided by the local Docker Compose environment.

## CI/CD flow

GitHub Actions currently performs the core validation and build flow:

```text
Push to main
   |
   v
Python validation
   |
   v
pytest
   |
   v
Training-data validation
   |
   v
Training
   |
   v
Model quality gate
   |
   v
Model registration
   |
   v
Build API image
   |
   v
Push image to GHCR
   |
   v
Update Kubernetes desired state
   |
   v
Flux reconciles Kubernetes
```

The model registry and Kubernetes deployment are intentionally separate concerns: MLflow tracks/registers/promotes the model, while the API container packages the model/runtime used by Kubernetes.
