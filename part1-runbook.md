# Part 1 Demo Runbook

## Setup

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create the local database and seed fake data:

```bash
python manage.py migrate
python manage.py seed_demo_data
```

Run the local server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/part1/
```

## SQL Injection

Safe ORM search:

```text
http://127.0.0.1:8000/part1/sql/safe/?q=public
```

Vulnerable raw SQL search:

```text
http://127.0.0.1:8000/part1/sql/vulnerable/?q=public
```

PoC:

```text
http://127.0.0.1:8000/part1/sql/vulnerable/?q=%27%20OR%201%3D1%20--
```

Fixed parameterized search:

```text
http://127.0.0.1:8000/part1/sql/fixed/?q=%27%20OR%201%3D1%20--
```

Expected teaching point:

> Keep user input as data, not query code.

## XSS

Upload a report file, then preview it:

```text
http://127.0.0.1:8000/part1/xss/upload/
```

Upload a malicious SVG (e.g. `<svg onload=alert(1)>`). Vulnerable preview

trusts the file content:

```text
http://127.0.0.1:8000/part1/xss/preview/?name=welcome.svg
```

Fixed preview escapes the content:

```text
http://127.0.0.1:8000/part1/xss/preview/fixed/?name=welcome.svg
```

Expected teaching point:

> User content should render as content, not code.

## CSRF

Protected form:

```text
http://127.0.0.1:8000/part1/csrf/safe/
```

Vulnerable endpoint:

```text
http://127.0.0.1:8000/part1/csrf/vulnerable/
```

Attack page:

```text
http://127.0.0.1:8000/part1/csrf/attack-page/
```

Fixed form:

```text
http://127.0.0.1:8000/part1/csrf/fixed/
```

Expected teaching point:

> A logged-in browser is not proof that the user intentionally made the request.

## CORS Clarification

This is a short explanation after CSRF, not a full live demo.

Use the snippets in:

```text
presentation-code-blocks.md
```

Expected teaching point:

> CORS controls who can read responses in the browser; CSRF controls whether state-changing requests require user intent.

## Clickjacking

Protected page:

```text
http://127.0.0.1:8000/part1/clickjacking/protected/
```

Header check:

```bash
curl -sS -i 'http://127.0.0.1:8000/part1/clickjacking/protected/' | grep -i '^X-Frame-Options:'
```

Expected teaching point:

> Some attacks trick the user into clicking the real app through a malicious frame.

## Open Redirect

Vulnerable redirect:

```text
http://127.0.0.1:8000/part1/redirect/vulnerable/?next=https://example.com
```

Fixed redirect:

```text
http://127.0.0.1:8000/part1/redirect/fixed/?next=https://example.com
```

Expected teaching point:

> The user can request where to go next, but the server must decide whether that destination is allowed.

## Deployment Security Settings

This is a short explanation, not a local HTTPS demo.

Show the snippets in:

```text
presentation-code-blocks.md
```

Expected teaching point:

> Django has settings for browser and transport protections, but they only work when deployment matches the assumptions.

## IDOR Bridge

Reference page:

```text
http://127.0.0.1:8000/part1/idor/reference/
```

Expected teaching point:

> Authentication answers "who are you?" Authorization answers "should you access this specific object?"
