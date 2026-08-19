from django.urls import path

from console import views


urlpatterns = [
    path("", views.frontend, name="frontend"),
    path("api/targets/", views.targets_api, name="targets_api"),
    path("api/diag/run/", views.diag_run_api, name="diag_run_api"),
    path("webhooks/test/", views.webhook_test_api, name="webhook_test_api"),
    path("internal/oncall-metrics/", views.oncall_metrics_api, name="oncall_metrics_api"),
    path("api/hints/", views.hints_api, name="hints_api"),
]