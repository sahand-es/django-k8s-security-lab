#!/usr/bin/env bash
set -euo pipefail

echo "=== backend-sa (saas-app) effective permissions ==="
kubectl auth can-i --list --as=system:serviceaccount:saas-app:backend-sa
echo
echo "=== backend-sa (internal-tools) effective permissions ==="
kubectl auth can-i --list --as=system:serviceaccount:internal-tools:backend-sa -n ctf-secrets
echo
echo "=== cluster-reader scope checks (saas-app backend-sa) ==="
kubectl auth can-i get nodes --as=system:serviceaccount:saas-app:backend-sa
kubectl auth can-i get secrets -A --as=system:serviceaccount:saas-app:backend-sa
kubectl auth can-i get pods -A --as=system:serviceaccount:saas-app:backend-sa
echo "--- write must be 'no' ---"
kubectl auth can-i create pods --as=system:serviceaccount:saas-app:backend-sa
kubectl auth can-i delete secrets --as=system:serviceaccount:saas-app:backend-sa
echo
echo "=== services (should be ClusterIP-only except backend) ==="
kubectl get svc -A | grep -E 'admin-panel|backend'
echo
echo "=== pods ==="
kubectl get pods -A | grep -E 'backend|admin-panel|legacy-worker'
echo
echo "=== automount check on backend pod ==="
kubectl get pods -n saas-app -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.automountServiceAccountToken}{"\n"}{end}'
echo
echo "=== resource quotas ==="
kubectl get resourcequota -A
echo
echo "=== worker activity feed ==="
kubectl -n saas-app exec deploy/backend -c worker -- python manage.py runworker --once 2>/dev/null || true
echo "(if the pod is up, GET /api/events shows the feed)"
