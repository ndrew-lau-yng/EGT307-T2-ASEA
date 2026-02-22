#!/bin/bash
set -e

echo "Starting Minikube..."
minikube start

echo "Enabling addons..."
minikube addons enable ingress
minikube addons enable metrics-server

echo "Waiting for ingress-nginx controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=Ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "Waiting for ingress-nginx controller deployment..."
kubectl wait -n ingress-nginx --for=condition=Available deployment \
  -l app.kubernetes.io/component=controller --timeout=180s

echo "Creating namespace egt307 (if it doesn't exists)..."
kubectl create namespace egt307 --dry-run=client -o yaml | kubectl apply -f -

echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/database-service/ -n egt307
kubectl apply -f k8s/inference-service/ -n egt307
kubectl apply -f k8s/api-gateway-service/ -n egt307
kubectl apply -f k8s/frontend-service/ -n egt307
kubectl apply -f k8s/ingress/ingress.yaml -n egt307

echo "Waiting for all pods to be Ready..."
kubectl wait --namespace egt307 \
  --for=condition=Ready pod \
  --all \
  --timeout=300s

echo "All pods are running and ready!"
kubectl get pods -n egt307

minikube service ingress-nginx-controller -n ingress-nginx --url 
echo "Minikube setup complete. You can access the application at the first URL."
