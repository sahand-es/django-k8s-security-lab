import os
import resource
import subprocess

import requests
import urllib3
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Event, Org, Report, User
from .serializers import AuthSerializer, PingSerializer, WebhookSerializer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPORT_DIR = "/app/reports"
PING_FLAG_PATH = "/opt/.sysdiag-7e3f9a2c4b1d8e5f/flag.txt"

FLAG_F3 = os.environ.get("FLAG_F3", "")
FLAG_F6 = os.environ.get("FLAG_F6", "")


def _get_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return request.COOKIES.get("ctf_token")


def _current_user(request):
    from config.jwt import decode

    token = _get_token(request)
    if not token:
        return None
    payload = decode(token)
    if not payload:
        return None
    try:
        return User.objects.get(pk=payload.get("sub"))
    except User.DoesNotExist:
        return None


# ---------- Template (HTML) views ----------

def index(request):
    if _current_user(request):
        return redirect("dashboard")
    return render(request, "index.html")


def dashboard(request):
    user = _current_user(request)
    if not user:
        return redirect("index")
    reports = Report.objects.filter(org=user.org)
    return render(request, "dashboard.html", {"user": user, "reports": reports, "active": "dashboard"})


def reports(request):
    user = _current_user(request)
    if not user:
        return redirect("index")
    reports = Report.objects.filter(org=user.org)
    return render(request, "reports.html", {"user": user, "reports": reports, "active": "reports"})


def ping_tool(request):
    user = _current_user(request)
    if not user:
        return redirect("index")
    return render(request, "ping.html", {"user": user, "active": "ping"})


def webhook_tool(request):
    user = _current_user(request)
    if not user:
        return redirect("index")
    return render(request, "webhook.html", {"user": user, "active": "webhook"})


def robots_txt(request):
    body = "User-agent: *\nDisallow: /api/schema/\nDisallow: /api/schema/swagger-ui/\nDisallow: /swagger.json\n"
    return HttpResponse(body, content_type="text/plain")


# ---------- API (DRF) views ----------

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=AuthSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT})
    def post(self, request):
        from config.jwt import create_token

        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        if not username or not password:
            return JsonResponse({"error": "username and password required"}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "username taken"}, status=400)
        if User.objects.count() >= 100:
            return JsonResponse({"error": "registration closed"}, status=403)
        org = Org.objects.order_by("pk").first()
        user = User.objects.create_user(username=username, password=password, org=org)
        token = create_token(user)
        resp = JsonResponse({"token": token})
        resp.set_cookie("ctf_token", token)
        return resp


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=AuthSerializer, responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT})
    def post(self, request):
        from config.jwt import create_token

        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = User.objects.filter(username=username).first()
        if not user or not user.check_password(password):
            return JsonResponse({"error": "invalid credentials"}, status=401)
        token = create_token(user)
        resp = JsonResponse({"token": token})
        resp.set_cookie("ctf_token", token)
        return resp


class AdminDashboardView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT})
    def get(self, request):
        from config.jwt import decode

        payload = decode(_get_token(request))
        if not payload or payload.get("role") != "admin":
            return JsonResponse({"error": "forbidden"}, status=403)
        return JsonResponse({"flag": FLAG_F6})


class InternalFlagView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter(name="X-Debug-Mode", type=str, location=OpenApiParameter.HEADER, required=False, description="Set to 'true' to enable debug mode.")],
        responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        if request.headers.get("X-Debug-Mode") == "true":
            return JsonResponse({"flag": FLAG_F3})
        return JsonResponse({"error": "forbidden"}, status=403)


class OrgReportView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("org_id", int, OpenApiParameter.PATH),
            OpenApiParameter("report_id", int, OpenApiParameter.PATH),
        ],
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, org_id, report_id):
        report = Report.objects.filter(pk=report_id, org_id=org_id).first()
        if not report:
            return JsonResponse({"error": "not found"}, status=404)
        return JsonResponse({"title": report.title, "secret_note": report.secret_note})


class ReportDownloadView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter("file", str, OpenApiParameter.QUERY, description="Report filename to download (served from /app/reports/).")],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        filename = request.query_params.get("file", "")
        path = os.path.join(REPORT_DIR, filename) if filename else REPORT_DIR
        if os.path.isdir(path):
            entries = sorted(os.listdir(path))
            body = f"Directory listing of {os.path.realpath(path)}\n\n" + "\n".join(entries) + "\n"
            return HttpResponse(body, content_type="text/plain")
        if not filename:
            return JsonResponse({"error": "file param required"}, status=400)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            return JsonResponse({"error": "file not found"}, status=404)
        return HttpResponse(content, content_type="text/plain")


class DiagPingView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=PingSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        host = request.data.get("host", "")
        if not host:
            return JsonResponse({"error": "host param required"}, status=400)

        def _limit():
            resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024 * 1024, 256 * 1024 * 1024))

        try:
            result = subprocess.run(
                f"ping -c 2 {host}",
                shell=True,
                capture_output=True,
                timeout=15,
                preexec_fn=_limit,
            )
        except subprocess.TimeoutExpired:
            return JsonResponse({"output": "command timed out"}, status=200)
        out = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        err = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        return JsonResponse({"output": out or err})


class WebhookTestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=WebhookSerializer, responses={(200, "text/plain"): OpenApiTypes.STR, 502: OpenApiTypes.OBJECT})
    def post(self, request):
        url = request.data.get("url", "")
        method = request.data.get("method", "GET")
        headers = request.data.get("headers", {}) or {}
        if not url:
            return JsonResponse({"error": "url param required"}, status=400)
        try:
            resp = requests.request(method, url, headers=headers, verify=False, timeout=3)
            return HttpResponse(resp.text, status=resp.status_code, content_type="text/plain")
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=502)


class EventsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        events = list(Event.objects.order_by("-created_at")[:50].values("kind", "message", "created_at"))
        return JsonResponse({"events": events})
