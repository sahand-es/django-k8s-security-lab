import ipaddress
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .models import Account, Document, Product


BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "demo_files" / "reports"
XSS_UPLOAD_DIR = BASE_DIR / "demo_files" / "xss_uploads"
ALLOWED_REPORTS = {
    "alice-summary": "alice-summary.txt",
    "public-status": "public-status.txt",
}
ALLOWED_DIAGNOSTIC_TARGETS = {"api", "worker", "database"}
ALLOWED_FETCH_PATHS = {"/part1/fetch/public-api/", "/part2/fetch/public-api/"}
ATTACKER_WEBHOOK_EVENTS = []
USER_PROJECTS = {
    "alice": {"project": "payments-preview", "environment": "preview-a"},
    "bob": {"project": "billing-preview", "environment": "preview-b"},
}


def index(request):
    return render(request, "demos/index.html")


def part2_index(request):
    return render(request, "demos/part2_index.html")


def sql_safe(request):
    q = request.GET.get("q", "")
    products = Product.objects.filter(name__icontains=q) | Product.objects.filter(description__icontains=q)
    return render(request, "demos/sql.html", {"title": "SQL safe ORM search", "q": q, "products": products})


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
    products = [{"id": row[0], "name": row[1], "owner": row[2], "description": row[3]} for row in rows]
    return render(request, "demos/sql.html", {"title": "SQL vulnerable raw search", "q": q, "products": products, "sql": sql})


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
    products = [{"id": row[0], "name": row[1], "owner": row[2], "description": row[3]} for row in rows]
    return render(request, "demos/sql.html", {"title": "SQL fixed parameterized search", "q": q, "products": products})


def xss_upload(request):
    if request.method == "POST":
        upload = request.FILES.get("upload")
        if upload:
            XSS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            name = os.path.basename(upload.name)
            path = XSS_UPLOAD_DIR / name
            with path.open("wb") as f:
                for chunk in upload.chunks():
                    f.write(chunk)
            return redirect(f"/part1/xss/preview/?name={name}")
    files = sorted(p.name for p in XSS_UPLOAD_DIR.glob("*")) if XSS_UPLOAD_DIR.exists() else []
    return render(request, "demos/xss_upload.html", {"title": "XSS upload report", "files": files})


def xss_safe(request):
    body = request.GET.get("body", "<b>Hello interns</b>")
    return render(request, "demos/xss.html", {"title": "XSS safe escaped rendering", "body": body})


def xss_vulnerable(request):
    body = request.GET.get("body", "<b>Hello interns</b>")
    rendered_body = mark_safe(body)
    return render(request, "demos/xss.html", {"title": "XSS vulnerable trusted rendering", "body": rendered_body})


def xss_fixed(request):
    body = request.GET.get("body", "<b>Hello interns</b>")
    rendered_body = format_html("{}", body)
    return render(request, "demos/xss.html", {"title": "XSS fixed escaped rendering", "body": rendered_body})


def _preview(request, trusted):
    name = os.path.basename(request.GET.get("name", ""))
    path = XSS_UPLOAD_DIR / name
    if not path.exists():
        return HttpResponse("No such upload")
    body = path.read_text(errors="replace")
    if trusted:
        body = mark_safe(body)
    return render(request, "demos/xss_preview.html", {"title": "XSS preview", "name": name, "body": body, "trusted": trusted})


def xss_preview_vulnerable(request):
    return _preview(request, trusted=True)


def xss_preview_fixed(request):
    return _preview(request, trusted=False)


@csrf_protect
def csrf_safe(request):
    account = _demo_account()
    if request.method == "POST":
        amount = int(request.POST.get("amount", "0"))
        account.balance -= amount
        account.save()
        return redirect("/part1/csrf/safe/")
    return render(request, "demos/csrf_form.html", {"title": "CSRF protected transfer", "account": account})


@csrf_exempt
def csrf_vulnerable(request):
    account = _demo_account()
    if request.method == "POST":
        amount = int(request.POST.get("amount", "0"))
        account.balance -= amount
        account.save()
        return HttpResponse(f"Transferred {amount}. New balance: {account.balance}")
    return render(request, "demos/csrf_form.html", {"title": "CSRF vulnerable transfer", "account": account})


@csrf_protect
def csrf_fixed(request):
    account = _demo_account()
    if request.method == "POST":
        amount = int(request.POST.get("amount", "0"))
        account.balance -= amount
        account.save()
        return redirect("/part1/csrf/fixed/")
    return render(request, "demos/csrf_form.html", {"title": "CSRF fixed transfer", "account": account})


def csrf_attack_page(request):
    target = request.build_absolute_uri("/part1/csrf/vulnerable/")
    return render(request, "demos/csrf_attack.html", {"target": target})


def clickjacking_protected(request):
    return render(request, "demos/clickjacking.html")


def redirect_vulnerable(request):
    next_url = request.GET.get("next", "/part1/")
    return redirect(next_url)


def redirect_fixed(request):
    next_url = request.GET.get("next", "/part1/")
    allowed = url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )
    if not allowed:
        next_url = "/part1/"
    return redirect(next_url)


def idor_reference(request):
    vulnerable = "document = Document.objects.get(id=document_id)"
    fixed = "document = get_object_or_404(Document, id=document_id, owner=request.user.username)"
    document = get_object_or_404(Document, owner="alice")
    return render(request, "demos/idor_reference.html", {"vulnerable": vulnerable, "fixed": fixed, "document": document})


def _demo_account():
    account, _ = Account.objects.get_or_create(owner="alice", defaults={"balance": 1000})
    return account


def file_vulnerable(request):
    name = request.GET.get("name", "alice-summary.txt")
    path = REPORT_DIR / name
    try:
        content = path.read_text()
    except OSError as exc:
        content = f"Could not read {path}: {exc}"
    return render(request, "demos/integration_result.html", {"title": "Path traversal vulnerable file read", "input": name, "result": content})


def file_fixed(request):
    report_id = request.GET.get("report", "alice-summary")
    filename = ALLOWED_REPORTS.get(report_id)
    if filename is None:
        content = "Unknown report"
    else:
        content = (REPORT_DIR / filename).read_text()
    return render(request, "demos/integration_result.html", {"title": "Path traversal fixed file read", "input": report_id, "result": content})


def subprocess_vulnerable(request):
    target = request.GET.get("target", "api")
    command = f"echo checking-{target}"
    completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=2)
    result = completed.stdout + completed.stderr
    return render(request, "demos/integration_result.html", {"title": "Subprocess vulnerable diagnostics", "input": command, "result": result})


def subprocess_blind(request):
    target = request.GET.get("target", "api")
    command = f"echo checking-{target}"
    try:
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        result = "Diagnostic accepted. Command output is not returned to the HTTP response."
    except subprocess.TimeoutExpired:
        result = "Diagnostic timed out. The response delay is the signal."
    return render(request, "demos/integration_result.html", {"title": "Subprocess blind command injection", "input": command, "result": result})


def subprocess_fixed(request):
    target = request.GET.get("target", "api")
    if target not in ALLOWED_DIAGNOSTIC_TARGETS:
        result = "Unknown diagnostic target"
    else:
        completed = subprocess.run(["printf", "checking %s\n", target], capture_output=True, text=True, timeout=2)
        result = completed.stdout + completed.stderr
    return render(request, "demos/integration_result.html", {"title": "Subprocess fixed diagnostics", "input": target, "result": result})


def fetch_vulnerable(request):
    url = request.GET.get("url", request.build_absolute_uri("/part2/fetch/public-api/"))
    result = _fetch_url(url)
    return render(request, "demos/integration_result.html", {"title": "SSRF vulnerable outbound fetch", "input": url, "result": result})


def fetch_fixed(request):
    url = request.GET.get("url", request.build_absolute_uri("/part2/fetch/public-api/"))
    if not _is_allowed_demo_fetch(url):
        result = "Blocked by outbound fetch policy"
    else:
        result = _fetch_url(url)
    return render(request, "demos/integration_result.html", {"title": "SSRF fixed outbound fetch", "input": url, "result": result})


def public_api(request):
    return HttpResponse("Public demo API response")


def internal_admin(request):
    return HttpResponse("Internal admin response: fake-secret-token=demo-only")


def attacker_sink(request):
    ATTACKER_WEBHOOK_EVENTS.append(request.GET.urlencode())
    return HttpResponse("ok")


def attacker_events(request):
    result = "\n".join(ATTACKER_WEBHOOK_EVENTS[-10:]) or "No webhook events received yet"
    return render(request, "demos/integration_result.html", {"title": "Attacker webhook events", "input": "/part2/webhooks/attacker-sink/", "result": result})


def task_vulnerable(request):
    action = request.GET.get("action", "export")
    document_id = request.GET.get("document_id", "1")
    result = _run_fake_task(action, document_id)
    return render(request, "demos/integration_result.html", {"title": "Task vulnerable parameter trust", "input": f"{action=} {document_id=}", "result": result})


def task_fixed(request):
    action = request.GET.get("action", "export")
    document = get_object_or_404(Document, owner="alice")
    if action != "export":
        result = "Unsupported task for this endpoint"
    else:
        result = _run_fake_task("export", str(document.id))
    return render(request, "demos/integration_result.html", {"title": "Task fixed parameter trust", "input": f"{action=} document_id={document.id}", "result": result})


def privileged_vulnerable(request):
    user = request.GET.get("user", "alice")
    target_user = request.GET.get("target_user", user)
    action = request.GET.get("action", "restart")
    result = _fake_control_plane_action(action, target_user)
    return render(request, "demos/integration_result.html", {"title": "Privileged integration vulnerable action", "input": f"{user=} {target_user=} {action=}", "result": result})


def privileged_fixed(request):
    user = request.GET.get("user", "alice")
    action = request.GET.get("action", "restart")
    if action != "restart":
        result = "Unsupported action for this endpoint"
    else:
        result = _fake_control_plane_action("restart", user)
    return render(request, "demos/integration_result.html", {"title": "Privileged integration fixed action", "input": f"{user=} {action=}", "result": result})


def _fetch_url(url):
    try:
        request = Request(url, headers={"User-Agent": "security-lab-demo"})
        with urlopen(request, timeout=2) as response:
            return response.read(500).decode("utf-8", errors="replace")
    except Exception as exc:
        return f"Fetch failed: {exc}"


def _is_allowed_demo_fetch(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.path not in ALLOWED_FETCH_PATHS:
        return False
    try:
        ip = ipaddress.ip_address(parsed.hostname or "")
    except ValueError:
        return parsed.hostname in {"localhost", "127.0.0.1"}
    return ip.is_loopback


def _run_fake_task(action, document_id):
    document = get_object_or_404(Document, id=document_id)
    if action == "export":
        return f"Exported document '{document.title}' owned by {document.owner}"
    if action == "email_owner":
        return f"Emailed document '{document.title}' to {document.owner}@example.test"
    return f"Unknown task action: {action}"


def _fake_control_plane_action(action, target_user):
    project = USER_PROJECTS.get(target_user)
    if project is None:
        return "Unknown target"
    if action == "restart":
        return f"Restarted {project['environment']} for project {project['project']}"
    if action == "snapshot":
        return f"Created privileged snapshot for project {project['project']}"
    return f"Unsupported privileged action: {action}"
