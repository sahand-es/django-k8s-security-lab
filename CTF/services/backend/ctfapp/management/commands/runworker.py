import time

import requests
import urllib3
from django.core.management.base import BaseCommand

from ctfapp.models import Event

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

K8S_API = "https://kubernetes.default.svc"
ESCAPE_ZONE_PODS = "/api/v1/namespaces/escape-zone/pods"
ADMIN_PANEL = "http://admin-panel.internal-tools.svc.cluster.local/"
TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
TICK = 25
MAX_EVENTS = 100


def _heartbeat_cluster():
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            token = f.read().strip()
        resp = requests.get(
            K8S_API + ESCAPE_ZONE_PODS,
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=4,
        )
        data = resp.json()
        names = [i.get("metadata", {}).get("name", "?") for i in data.get("items", [])]
        count = len(names)
        detail = ", ".join(names[:3]) if names else "none"
        Event.objects.create(kind="cluster", message=f"k8s health: {count} pod(s) in escape-zone ({detail})")
    except Exception as exc:
        Event.objects.create(kind="cluster", message=f"k8s health check failed: {str(exc)[:80]}")


def _heartbeat_integration():
    try:
        resp = requests.get(ADMIN_PANEL, verify=False, timeout=4)
        ok = resp.status_code == 200
        Event.objects.create(
            kind="integration",
            message=f"integration ping -> admin-panel: {'ok' if ok else 'http ' + str(resp.status_code)}",
        )
    except Exception as exc:
        Event.objects.create(kind="integration", message=f"integration ping failed: {str(exc)[:80]}")


def _prune():
    excess = Event.objects.count() - MAX_EVENTS
    if excess > 0:
        ids = list(Event.objects.order_by("created_at").values_list("pk", flat=True)[:excess])
        Event.objects.filter(pk__in=ids).delete()


class Command(BaseCommand):
    help = "Background worker: periodic real-access heartbeat into the Activity feed"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="run a single tick then exit")

    def handle(self, *args, **options):
        Event.objects.create(kind="report", message="worker started; beginning platform heartbeats")
        while True:
            _heartbeat_cluster()
            _heartbeat_integration()
            _prune()
            if options.get("once"):
                break
            time.sleep(TICK)
