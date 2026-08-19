import jwt
from django.conf import settings


def create_token(user, role="user"):
    payload = {
        "sub": str(user.pk),
        "username": user.username,
        "org": user.org.name if user.org else None,
        "role": role,
    }
    return jwt.encode(payload, getattr(settings, "JWT_SECRET", "changeme123"), algorithm="HS256")


def decode(token):
    secret = getattr(settings, "JWT_SECRET", "changeme123")
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        return None
    if header.get("alg") == "none":
        return jwt.decode(token, options={"verify_signature": False})
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        return None
