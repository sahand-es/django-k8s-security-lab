from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.urls import path

from . import views


class SchemaJsonView(SpectacularAPIView):
    renderer_classes = [OpenApiJsonRenderer]
    name = "Schema (JSON)"


urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("reports", views.reports, name="reports"),
    path("tools/ping", views.ping_tool, name="ping_tool"),
    path("tools/webhook", views.webhook_tool, name="webhook_tool"),
    path("robots.txt", views.robots_txt, name="robots_txt"),

    path("auth/register", views.RegisterView.as_view(), name="register"),
    path("auth/login", views.LoginView.as_view(), name="login"),
    path("admin/dashboard", views.AdminDashboardView.as_view(), name="admin_dashboard"),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("swagger.json", SchemaJsonView.as_view(), name="swagger-json"),

    path("api/internal/flag", views.InternalFlagView.as_view(), name="internal_flag"),
    path("api/orgs/<int:org_id>/reports/<int:report_id>", views.OrgReportView.as_view(), name="org_report"),
    path("api/reports/download", views.ReportDownloadView.as_view(), name="report_download"),
    path("api/diag/ping", views.DiagPingView.as_view(), name="diag_ping"),
    path("api/webhooks/test", views.WebhookTestView.as_view(), name="webhook_test"),
    path("api/events", views.EventsView.as_view(), name="events"),
]
