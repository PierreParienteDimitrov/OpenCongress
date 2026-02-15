"""
Django production settings for CongressTrack project.
"""

import os

import sentry_sdk  # type: ignore[import-not-found]
from sentry_sdk.integrations.celery import CeleryIntegration  # type: ignore[import-not-found]
from sentry_sdk.integrations.django import DjangoIntegration  # type: ignore[import-not-found]

from .base import *  # noqa: F401, F403

DEBUG = False

INSTALLED_APPS += ["schema_graph"]  # noqa: F405

# Require critical secrets in production — fail fast if missing
_REQUIRED_SECRETS = [
    "SECRET_KEY",
    "AUTH_SYNC_SECRET",
    "REVALIDATION_SECRET",
    "ENCRYPTION_KEY",
]
for _var in _REQUIRED_SECRETS:
    _val = os.environ.get(_var, "")
    if not _val or _val.startswith("django-insecure") or _val.startswith("dev-"):
        raise ValueError(f"Production requires a secure {_var} environment variable")

# Override base settings with validated production values
SECRET_KEY = os.environ["SECRET_KEY"]
AUTH_SYNC_SECRET = os.environ["AUTH_SYNC_SECRET"]
REVALIDATION_SECRET = os.environ["REVALIDATION_SECRET"]

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",") + [
    "api.opencongress.app",
    "congresstrack-api-production.up.railway.app",
]

# Database - PostgreSQL
# Railway provides DATABASE_URL; parse it if available, otherwise fall back to individual vars
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import urllib.parse

    parsed = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or 5432),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "congresstrack"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",
            },
        }
    }

# CORS - Allow Vercel preview deployments and production domains
CORS_ALLOWED_ORIGINS = [
    "https://opencongress.app",
    "https://www.opencongress.app",
]

# Allow Vercel preview URLs (*.vercel.app)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]
CORS_ALLOW_CREDENTIALS = True

# Security
# SSL is terminated at Railway's load balancer — don't redirect at the app level
# or internal healthchecks will fail (they hit http://localhost internally)
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    "https://api.opencongress.app",
    "https://congresstrack-api-production.up.railway.app",
]

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN and SENTRY_DSN.startswith("https://"):

    def _before_send(event, hint):
        """Filter out noise from health check endpoints."""
        request_url = event.get("request", {}).get("url", "")
        if request_url.endswith(("/api/health/", "/api/ready/")):
            return None
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=os.environ.get("ENVIRONMENT", "production"),
        release=os.environ.get("RELEASE_VERSION", ""),
        send_default_pii=False,
        before_send=_before_send,
    )

# Email
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "apikey")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@congresstrack.org")
