from django.urls import path

from vault import views


urlpatterns = [
    path("", views.frontend, name="frontend"),
    path("api/session/", views.session_api, name="session_api"),
    path("api/queues/<int:queue_id>/", views.queue_api, name="queue_api"),
    path("api/tickets/search/", views.ticket_search_api, name="ticket_search_api"),
    path("api/tickets/<int:ticket_id>/", views.ticket_api, name="ticket_api"),
    path("back/", views.back_hop, name="back_hop"),
    path("api/hints/", views.hints_api, name="hints_api"),
    path("staff/handover/<int:ticket_id>/", views.staff_handover, name="staff_handover"),
]
