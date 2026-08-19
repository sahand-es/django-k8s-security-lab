# CTF — Kind setup runbook

End-to-end: bring up a kind cluster, install ingress, deploy the CTF, verify. Assumes you run this on the host that runs Docker (the "VM").

## Prereqs
```bash
# install if missing (Ubuntu VM)
# Docker: https://docs.docker.com/engine/install/ubuntu/
sudo apt-get update && sudo apt-get install -y docker.io kubectl
sudo usermod -aG docker ubuntu && newgrp docker
# kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64 && chmod +x kind && sudo mv kind /usr/local/bin/
# helm (for Traefik)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
docker --version; kind version; kubectl version --client; helm version
```

## 1. Create the kind cluster
`kind-config.yaml` creates 3 nodes (control-plane + 2 workers). The control-plane maps host 80→30080 and 443→30443 (Traefik's NodePorts). `ctf-worker2` mounts the host docker socket (F11 escape vector).

```bash
cd CTF
kind create cluster --name ctf --config kind-config.yaml
kubectl cluster-info --context kind-ctf
kubectl get nodes
# expect: ctf-control-plane, ctf-worker, ctf-worker2
```

## 2. Install Traefik ingress controller
Install via Helm as NodePort 30080/30443 (matching the kind port mappings), and make it the default IngressClass:

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm install traefik traefik/traefik \
  --namespace traefik --create-namespace \
  --set ingressClass.enabled=true \
  --set ingressClass.isDefaultClass=true \
  --set service.type=NodePort \
  --set ports.web.nodePort=30080 \
  --set ports.websecure.nodePort=30443
kubectl wait --namespace traefik \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=traefik \
  --timeout=120s
```
The backend Ingress (`ctf.localhost`) uses `ingressClassName: traefik`; host:80 → kind:30080 → Traefik → backend service.

## 3. DNS for `ctf.localhost`
Point the hostname at the kind node (your host):
```bash
echo "127.0.0.1 ctf.localhost" | sudo tee -a /etc/hosts
# verify
ping -c1 ctf.localhost
```
(If running on a remote VM, use the VM's IP instead of 127.0.0.1.)

## 4. Build and load images into kind
```bash
./scripts/build_and_load.sh
```
Builds `ctf/backend` (with `kubectl`, `curl`, `ping`, `jq`), `ctf/admin-panel`, and `ctf/escape-zone` (with `curl`) and loads each into the kind container runtime (kind doesn't pull from a registry by default).

## 5. Deploy everything
```bash
./scripts/deploy_all.sh
```
Order (matters): namespaces → quotas → RBAC → `ctf-secrets` → `internal-tools` → `escape-zone` → `backend`. Also writes the F11 bonus flag to `~/flag.txt` on the host.

Notes:
- **F10** (`flag.txt` on the node) is self-placed by the `legacy-worker` initContainer — no manual step.
- **F11** (`~/flag.txt` on the VM host) is placed by `deploy_all.sh`. (Bonus, unadvertised.)

## 6. Wait for rollout, then verify
```bash
kubectl -n saas-app rollout status deploy/backend
kubectl -n internal-tools rollout status deploy/admin-panel
kubectl -n escape-zone rollout status pod legacy-worker      # it's a Pod, not a Deployment

./scripts/verify.sh
```
`verify.sh` checks:
- `backend-sa` (saas-app) is bound to the cluster-wide `cluster-reader` role: can `get/list/watch` **all** resources anywhere (nodes, secrets, pods, deployments, …) but cannot create/delete anything.
- `backend-sa` (saas-app) can `get/list pods` + `create pods/exec` in `escape-zone`.
- `backend-sa` (internal-tools) also gets cluster-reader (get/list/watch) cluster-wide.
- Services are ClusterIP-only (admin-panel) except `backend`.
- Quotas applied; backend pod automounts its SA token.

## 7. Smoke test
```bash
# frontend
curl -sI http://ctf.localhost/ | head -1
# swagger UI
curl -sI http://ctf.localhost/api/schema/swagger-ui/ | head -1
# worker Activity feed (should show real k8s + admin-panel reach after ~25s)
curl -s http://ctf.localhost/api/events | head -c 400
```

## 8. Reset / teardown
```bash
# full teardown
kind delete cluster --name ctf
# soft reset (keep cluster, wipe app)
kubectl delete -k k8s/backend; kubectl delete -k k8s/internal-tools; kubectl delete -k k8s/escape-zone; kubectl delete -k k8s/ctf-secrets
# then re-run deploy_all.sh
```
SQLite is ephemeral — it lives on a shared `emptyDir` mounted at `/app/db` (`SQLITE_PATH=/app/db/db.sqlite3`) so the web + worker sidecar share one DB. Deleting the backend pod resets the DB + Activity feed; the feed repopulates within ~25s via the worker.

## File map (this phase)
```
CTF/
├── kind-config.yaml          # 3 nodes, 80/443 port mappings, worker2 docker.sock
├── k8s/
│   ├── 00-namespaces.yaml
│   ├── 01-quotas.yaml
│   ├── 03-rbac.yaml              # cluster-reader CR/CRB + pod-exec-log role
│   ├── backend/                  # web + worker sidecar, Ingress, ClusterIP
│   ├── internal-tools/           # admin-panel (+ its own backend-sa)
│   ├── ctf-secrets/              # flag-secret
│   └── escape-zone/              # legacy-worker pod (F10 self-placed)
└── scripts/
    ├── build_and_load.sh         # builds ctf/{backend,admin-panel,escape-zone}
```

## How the deployed pieces map to flags
- **F1** docker layer leak → `ctf/backend` image history.
- **F2/F3** swagger + hidden route → backend Ingress (`/api/schema/swagger-ui/`, `/api/internal/flag`).
- **F4** traversal → backend (`/app/flag.txt`, self-discovering dir-listing).
- **F5** IDOR → backend (Org A user reads Org B report).
- **F6** JWT → backend (`/admin/dashboard`).
- **F7** SSRF → backend webhook tester → `admin-panel` ClusterIP (internal-tools).
- **F8** SSRF → steal the pod's `backend-sa` token (F9 RCE) → k8s API → `flag-secret` (ctf-secrets); token is cluster-reader.
- **F9** RCE → backend (`/opt/.sysdiag-…/flag.txt`).
- **F10** node escape → `legacy-worker` (escape-zone), reached via backend-sa `pods/exec`; flag at `/var/lib/node-data/flag.txt` on the node (self-placed by initContainer). Inside the pod the hostPath mount is `/host/...`, so exec reads `/host/var/lib/node-data/flag.txt`.
- **F11** docker.sock → `ctf-worker2` mounts host docker.sock; flag at `~/flag.txt` on the VM host.

The worker sidecar visibly exercises the backend's real access (k8s API + admin-panel) in the Activity feed — the same reach F7/F8/F10 abuse.
