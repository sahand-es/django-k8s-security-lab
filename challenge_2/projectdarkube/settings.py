import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "challenge-local-demo-secret")
DEBUG = os.environ.get("DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = [origin for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if origin]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "console",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "projectdarkube.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

WSGI_APPLICATION = "projectdarkube.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ONCALL_USER = "intern"
ONCALL_SHIFT = "shadow · 18:00–00:00 IRST"

ONCALL_DIR = Path(os.environ.get("ONCALL_DIR", str(BASE_DIR / "deploy")))
DIAG_SCRIPT = str(ONCALL_DIR / "run" / "diagnostic.py")
FLAG_PATH = str(BASE_DIR / "flag.txt")
DIAG_TARGETS = ["api", "worker", "database", "scheduler"]

FLAGS = [f.strip() for f in os.environ.get("TEAM_FLAGS", "").split(",") if f.strip()]

HINTS = [
    "The diagnostic runner builds a shell command by hand and runs it with shell=True. The preview only truncates the display, not the command.",
    "A direct read only reveals half of the token — the rest is cut from the preview. For the full token, have the injected command send the output to a webhook or listener you control.",
    "/internal/oncall-metrics/ only answers requests that appear to come from the backend's own network. The webhook tester makes requests from exactly that position.",
]