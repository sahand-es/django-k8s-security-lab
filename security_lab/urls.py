from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/part1/", permanent=False)),
    path("part1/", include("demos.urls")),
    path("part2/", include("demos.urls")),
]
