from django.db import connection
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Queue, Ticket

CURRENT_USER = "intern"

HINTS = [
    "The ticket search box is just a UI. /api/tickets/search/ builds the SQL by hand — look at how q is placed into the LIKE.",
    "Ticket detail looks up by external_id with no queue scope. Any leaked id is enough.",
    "Direct access to /staff/handover/ is blocked. But /back/?next=... grants staff access when next starts with /staff/ — and next is user-controlled.",
]


def frontend(request):
    return render(request, "index.html")


def hints_api(request):
    return JsonResponse({"hints": HINTS})


def session_api(request):
    queue = get_object_or_404(Queue, member_username=CURRENT_USER)
    return JsonResponse(
        {
            "user": CURRENT_USER,
            "queue": {
                "id": queue.external_id,
                "name": queue.name,
                "squad": queue.squad,
            },
        }
    )


def queue_api(request, queue_id):
    queue = get_object_or_404(Queue, external_id=queue_id, member_username=CURRENT_USER)
    tickets = [
        {"id": t.external_id, "title": t.title, "summary": t.summary}
        for t in queue.tickets.filter(visible_in_frontend=True)
    ]
    return JsonResponse(
        {
            "id": queue.external_id,
            "name": queue.name,
            "squad": queue.squad,
            "note": queue.dashboard_note,
            "tickets": tickets,
        }
    )


def ticket_search_api(request):
    queue = get_object_or_404(Queue, member_username=CURRENT_USER)
    q = request.GET.get("q", "")
    sql = f"""
        SELECT external_id, title, summary
        FROM vault_ticket
        WHERE queue_id = {queue.id}
        AND visible_in_frontend = 1
        AND title LIKE '%{q}%'
    """
    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
    results = [{"id": row[0], "title": row[1], "summary": row[2]} for row in rows]
    return JsonResponse({"q": q, "results": results})


def ticket_api(request, ticket_id):
    ticket = get_object_or_404(Ticket, external_id=ticket_id)
    data = {
        "id": ticket.external_id,
        "title": ticket.title,
        "summary": ticket.summary,
        "staff_only": ticket.staff_only,
        "body": ticket.body,
    }
    if ticket.staff_only:
        data["handover_url"] = f"/staff/handover/{ticket.external_id}/"
    return JsonResponse(data)


def back_hop(request):
    next_url = request.GET.get("next", "/")
    response = redirect(next_url)
    if next_url.startswith("/staff/"):
        response.set_signed_cookie("staff_nav", "granted", httponly=True, samesite="Lax")
    return response


def staff_handover(request, ticket_id):
    if request.get_signed_cookie("staff_nav", default="") != "granted":
        return HttpResponseForbidden(
            "Staff handover is only reachable through the app's navigation hop."
        )
    ticket = get_object_or_404(Ticket, external_id=ticket_id, staff_only=True)
    return render(request, "handover.html", {"note": ticket.handoff_note, "ticket_id": ticket_id})
