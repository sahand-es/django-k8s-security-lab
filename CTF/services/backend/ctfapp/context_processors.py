from config.jwt import decode
from ctfapp.models import User


def current_user(request):
    token = request.COOKIES.get("ctf_token") or (
        request.META.get("HTTP_AUTHORIZATION", "").removeprefix("Bearer ").strip()
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer ")
        else None
    )
    if not token:
        return {"current_user": None, "current_org": None}
    payload = decode(token)
    if not payload:
        return {"current_user": None, "current_org": None}
    try:
        user = User.objects.get(pk=payload.get("sub"))
    except User.DoesNotExist:
        return {"current_user": None, "current_org": None}
    return {
        "current_user": user,
        "current_org": user.org,
    }
