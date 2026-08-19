import os
import subprocess
import urllib.request

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render

METRICS = {
    "service": "control-plane",
    "region": "tehran-1",
    "cluster": "lab-cluster",
    "flag_present": True,
    "note": "Internal operator metrics. Only reachable from the backend's own network.",
}


def flag_at(index):
    flags = getattr(settings, "FLAGS", [])
    return flags[index] if len(flags) > index else "run seed_challenge to set this flag"


def frontend(request):
    return render(request, "index.html")


def hints_api(request):
    return JsonResponse({"hints": settings.HINTS})


def targets_api(request):
    return JsonResponse(
        {
            "user": settings.ONCALL_USER,
            "shift": settings.ONCALL_SHIFT,
            "targets": settings.DIAG_TARGETS,
        }
    )


def preview_for(output):
    for flag in getattr(settings, "FLAGS", []):
        idx = output.find(flag)
        if idx != -1:
            return output[: idx + len(flag) // 2], "token"
    return output, None


def diag_run_api(request):
    target = request.GET.get("target", "")
    command = f"python3 {settings.DIAG_SCRIPT} {target}"
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=3)
        output = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        output = ""
    preview, cut = preview_for(output)
    return JsonResponse(
        {
            "target": target,
            "preview": preview,
            "note": (
                "Output truncated."
                if cut == "token"
                else "Diagnostic finished."
            ),
        }
    )


def webhook_test_api(request):
    url = request.GET.get("url", "")
    if not url:
        return JsonResponse({"error": "Missing url parameter."}, status=400)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CloudOps-webhook-tester/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = resp.read(2000).decode("utf-8", "replace")
        return JsonResponse({"status": resp.status, "body": body[:2000]})
    except Exception as exc:
        return JsonResponse({"error": f"{type(exc).__name__}: {exc}"}, status=400)


def oncall_metrics_api(request):
    remote = request.META.get("REMOTE_ADDR", "")
    if remote not in ("127.0.0.1", "::1"):
        return HttpResponseForbidden(
            "internal/oncall-metrics is only reachable from the backend's own network."
        )
    return JsonResponse(
        {**METRICS, "flag": flag_at(1)}
    )