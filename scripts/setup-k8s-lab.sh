#!/usr/bin/env bash

set -euo pipefail

echo "=========================================="
echo " MLOps Production Lab - Kubernetes Setup"
echo "=========================================="

echo
echo "==> 1. Checking Kubernetes"
kubectl version --client
kubectl get nodes

echo
echo "==> 2. Checking Flux CLI"

if command -v flux >/dev/null 2>&1; then
    echo "Flux CLI already installed:"
    flux --version
else
    echo "Flux CLI not found. Installing..."
    curl -s https://fluxcd.io/install.sh | sudo bash
    flux --version
fi

echo
echo "==> 3. Checking Flux prerequisites"
flux check --pre

echo
echo "==> 4. Checking Flux installation in cluster"

if kubectl get deployment source-controller -n flux-system >/dev/null 2>&1; then
    echo "Flux is already installed in the cluster."
else
    echo "Flux is not installed. Installing..."
    flux install
fi

echo
echo "==> 5. Waiting for Flux controllers"

kubectl wait \
    --for=condition=Available \
    deployment/source-controller \
    deployment/kustomize-controller \
    deployment/helm-controller \
    deployment/notification-controller \
    -n flux-system \
    --timeout=120s

echo
echo "==> 6. Verifying Flux"

flux check

echo
echo "==> 7. Flux controllers"

kubectl get pods -n flux-system

echo
echo "==> 8. Kubernetes nodes"

kubectl get nodes

echo
echo "=========================================="
echo " Kubernetes + Flux lab setup complete"
echo "=========================================="