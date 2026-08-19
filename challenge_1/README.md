# Support desk · the intern ticket queue

A short Django backend security challenge set in a CloudOps Level-1 support console. Source-visible (whitebox): find where the code leaves Django's safety rails, then prove each consequence.

You are an `intern` on a support rotation. The desk shows only your queue and your assigned tickets — that's normal behaviour. The story: *you can suddenly see more than your queue.*

## Run locally

```bash
export TEAM_FLAGS='FLAG{sqli_leak},FLAG{idor_peek},FLAG{redirect_take}'
python manage.py migrate
python manage.py seed_challenge
python manage.py runserver 0.0.0.0:8000
```

## Docker

```bash
docker build -t support-desk-challenge .
docker run --rm -p 8000:8000 \
  -e TEAM_FLAGS='FLAG{sqli_leak},FLAG{idor_peek},FLAG{redirect_take}' \
  support-desk-challenge
```

## Normal behaviour (the app works)

- **Ticket search** returns your queue's assigned tickets.
- **Ticket detail** opens the tickets assigned to you.
- **Back to dashboard** (`/back/?next=/`) hops you safely back to the console.

The bugs only surface when you deviate from these normal paths — guided by reading the source.

## Intended path

Three independent flags, one per vulnerability. Each sits inside the data its step returns, so capture is immediate and per-vulnerability.

1. **SQL injection** — `/api/tickets/search/` interpolates `q` into a raw `LIKE` instead of using the ORM.
   ```
   GET /api/tickets/search/?q=' OR 1=1 --
   ```
   Leaks the staff-only `P0 archive sync stalled` ticket. Its `summary` holds **flag 1**. Note its `id` — that's the internal ticket handle.

2. **IDOR** — `/api/tickets/<ticket_id>/` looks the ticket up by `external_id` with no queue/ownership scope. Open the leaked handle:
   ```
   GET /api/tickets/<leaked_id>/
   ```
   Returns the P0 incident thread body, which holds **flag 2** and mentions the staff handover page at `/staff/handover/<leaked_id>/`.

3. **Open redirect / workflow trust** — `/staff/handover/<leaked_id>/` is a staff-only page that returns `403` on direct access. The app's navigation hop at `/back/?next=...` grants staff access (via a `staff_nav` cookie) when `next` starts with `/staff/`. Since `next` is user-controlled, drive the hop to grant yourself access:
   ```
   GET /staff/handover/<leaked_id>/              # → 403 (direct access blocked)
   GET /back/?next=https://evil.com              # proves the redirect is genuinely open
   GET /back/?next=/staff/handover/<leaked_id>/  # sets the staff_nav cookie, then redirects
   GET /staff/handover/<leaked_id>/              # now renders with flag 3
   ```

## Hints

A static, always-available list at `GET /api/hints/` (no UI link, no counter):

- How `q` is placed into the SQL in `/api/tickets/search/`.
- The ticket detail lookup has no queue scope.
- Direct access to `/staff/handover/<id>/` is blocked, but `/back/?next=...` grants staff access when `next` starts with `/staff/` — and `next` is user-controlled.

## Notes

- The frontend's "only opens tickets assigned to this intern" guard is client-side only. The backend is the real authority.
- The hidden ticket id is derived from a hash of the three flags, so read it from step 1's response rather than guessing.
- Each flag is a full `FLAG{...}` value; submit each to the scoreboard independently.
