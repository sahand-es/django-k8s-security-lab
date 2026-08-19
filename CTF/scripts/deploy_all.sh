#!/usr/bin/env bash
set -euo pipefail

CTF_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CTF_ROOT"

echo ">>> namespaces"
kubectl apply -f k8s/00-namespaces.yaml

echo ">>> resource quotas"
kubectl apply -f k8s/01-quotas.yaml

echo ">>> RBAC (service accounts, roles, bindings)"
kubectl apply -f k8s/03-rbac.yaml

echo ">>> ctf-secrets (flag-secret)"
kubectl apply -k k8s/ctf-secrets

echo ">>> internal-tools (admin-panel)"
kubectl apply -k k8s/internal-tools

echo ">>> escape-zone (legacy-worker)"
kubectl apply -k k8s/escape-zone

echo ">>> backend (web + worker sidecar, ingress)"
kubectl apply -k k8s/backend

echo ">>> F11 bonus flag on the VM host (~flag.txt)"
echo "${FLAG_F11:-FLAG{d0ck3r_s0ck3t_1s_th3_r34l_r00t}}" > "$HOME/flag.txt"

echo
echo "Deployed. Frontend: http://ctf.localhost/  (add '127.0.0.1 ctf.localhost' to /etc/hosts if local)"
