#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="mlops"

log() {
  printf '\n==> %s\n' "$1"
}

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

command -v kubectl >/dev/null 2>&1 || fail "kubectl is required."
command -v curl >/dev/null 2>&1 || fail "curl is required."

if [[ -z "${GITHUB_PAT:-}" ]]; then
  printf 'GitHub PAT (read access to the private repository): '
  read -rs GITHUB_PAT
  printf '\n'
fi

[[ -n "$GITHUB_PAT" ]] || fail "A GitHub PAT is required."

log "1. Verify Kubernetes"
kubectl cluster-info >/dev/null
kubectl get nodes

log "2. Install Flux CLI if needed"
if ! command -v flux >/dev/null 2>&1; then
  curl -s https://fluxcd.io/install.sh | bash
fi
flux --version

log "3. Install / reconcile Flux controllers"
flux install
kubectl -n flux-system wait --for=condition=Ready pod --all --timeout=180s

log "4. Create application namespace"
kubectl apply -f "$REPO_ROOT/k8s/namespace.yaml"

log "5. Configure GitHub authentication"
kubectl -n "$NAMESPACE" create secret generic github-auth \
  --from-literal=username="${GITHUB_USERNAME:-shaikhtousif1}" \
  --from-literal=password="$GITHUB_PAT" \
  --dry-run=client -o yaml | kubectl apply -f -

log "6. Configure Flux GitRepository"
kubectl apply -f "$REPO_ROOT/flux/git-repository.yaml"

log "7. Configure Flux Kustomization"
kubectl apply -f "$REPO_ROOT/flux/kustomization.yaml"

log "8. Reconcile Flux"
flux reconcile source git mlops-production-lab -n "$NAMESPACE" --with-source
flux reconcile kustomization mlops-production-lab -n "$NAMESPACE" --with-source

log "9. Verify Flux"
flux get sources git -n "$NAMESPACE"
flux get kustomizations -n "$NAMESPACE"

log "10. Wait for application"
kubectl -n "$NAMESPACE" rollout status deployment/customer-churn-api --timeout=180s
kubectl -n "$NAMESPACE" wait --for=condition=Ready pod -l app=customer-churn-api --timeout=180s

log "11. Final application state"
kubectl get deployment,pods,svc -n "$NAMESPACE" -o wide

echo
echo "Deployed image:"
kubectl -n "$NAMESPACE" get deployment customer-churn-api \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'

echo
echo "=========================================="
echo " MLOps Kubernetes + Flux lab is READY"
echo "=========================================="
