import time
from functools import wraps

LIMIT = 30
WINDOW = 60
_hits = {}


def rate_limit(path):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            ip = request.META.get("REMOTE_ADDR", "unknown")
            key = f"{path}:{ip}"
            now = time.time()
            _hits[key] = [t for t in _hits.get(key, []) if now - t < WINDOW]
            if len(_hits[key]) >= LIMIT:
                from django.http import JsonResponse

                return JsonResponse({"error": "rate limited"}, status=429)
            _hits[key].append(now)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
