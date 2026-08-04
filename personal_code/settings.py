"""
Django settings for the Fully Alive Retreat site.

Every environment-specific value is read from the environment (loaded from a
local ``.env`` file in development). See ``.env.example`` for the full list.

Nothing in this file may contain a secret. If a required secret is missing the
project refuses to boot rather than falling back to an insecure default.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a boolean from the environment. Accepts 1/true/yes/on."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=()):
    """Read a comma-separated list from the environment."""
    raw = os.getenv(name)
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_required(name):
    """Read a value that the site cannot safely run without."""
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(
            f"The {name} environment variable is required but is not set. "
            f"See .env.example."
        )
    return value


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", default=False)

# In DEBUG an ephemeral key is acceptable; in production a missing key is fatal.
if DEBUG:
    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or "insecure-development-key-not-for-production"
else:
    SECRET_KEY = env_required("DJANGO_SECRET_KEY")

DOMAIN = os.getenv("DJANGO_DOMAIN", "fullyaliveretreat.com")

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"] if DEBUG else [DOMAIN, f"www.{DOMAIN}", ".herokuapp.com"],
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[f"https://{DOMAIN}", f"https://www.{DOMAIN}", "https://*.herokuapp.com"],
)

ROOT_URLCONF = "personal_code.urls"
WSGI_APPLICATION = "personal_code.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The admin lives at a configurable path so it is not trivially discoverable.
ADMIN_URL = os.getenv("DJANGO_ADMIN_URL", "admin").strip("/")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "registration.apps.RegistrationConfig",
    "personal_code.apps.PayPalIpnConfig",
    "axes",
]

MIDDLEWARE = [
    # SecurityMiddleware must run before WhiteNoise so that security headers are
    # applied to static responses too.
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # AxesMiddleware must come last so it sees the outcome of authentication.
    "axes.middleware.AxesMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "registration.context_processors.site_context",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=not DEBUG and bool(os.getenv("DATABASE_URL")),
    )
}

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend must be first so lockouts are enforced before any
    # password hashing happens.
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "camper_info"
LOGOUT_REDIRECT_URL = "home"

# django-axes: lock an offending IP/username pair out after repeated failures.
AXES_FAILURE_LIMIT = int(os.getenv("AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = "lockout.html"
AXES_IPWARE_PROXY_COUNT = 1 if os.getenv("DATABASE_URL") else None

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 12  # 12 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_HTTPONLY = False  # the CSRF cookie is read by no JS, but Django needs it readable for forms
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Reject oversized posts early. The registration form is small.
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100

if not DEBUG:
    # Heroku terminates TLS at the router and forwards the scheme in a header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", str(60 * 60 * 24 * 365)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
# The retreat is held on the Oregon coast; all camp-relative dates are local.
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Hashed filenames are content-addressed, so they can be cached indefinitely.
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

# Transactional camper mail is sent through Gmail via yagmail.
FAR_EMAIL_ADDRESS = os.getenv("FAR_EMAIL_ADDRESS", "fullyaliveretreat@gmail.com")
FAR_EMAIL_APP_PASSWORD = os.getenv("FAR_EMAIL_APP_PASSWORD", "")

# Django's own mail (error reports) uses the console in development.
EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend"
)
DEFAULT_FROM_EMAIL = FAR_EMAIL_ADDRESS
SERVER_EMAIL = FAR_EMAIL_ADDRESS
ADMINS = [("Site admin", email) for email in env_list("DJANGO_ADMIN_EMAILS")]

# ---------------------------------------------------------------------------
# PayPal
# ---------------------------------------------------------------------------

PAYPAL_TEST = env_bool("PAYPAL_TEST", default=DEBUG)
PAYPAL_RECEIVER_EMAIL = os.getenv("PAYPAL_RECEIVER_EMAIL", "nwasbc.youth@gmail.com")
PAYPAL_CURRENCY = "USD"

# The IPN listener path. Kept out of source so it can be rotated independently.
PAYPAL_ENDPOINT = os.getenv("PAYPAL_ENDPOINT", "paypal-ipn" if DEBUG else "")

# ---------------------------------------------------------------------------
# Site metadata
# ---------------------------------------------------------------------------

SITE_NAME = "Fully Alive Retreat"
SITE_TAGLINE = (
    "A Christian retreat for young adults to know God more deeply "
    "and share fellowship with one another."
)
INSTAGRAM_URL = "https://www.instagram.com/fullyaliveretreat"
TELEGRAM_URL = "https://t.me/+Ky9V40c6bh0yMjMx"
VIDEO_URL = "https://youtu.be/ztPhKAuXx5I"
CONTACT_EMAIL = os.getenv("FAR_CONTACT_EMAIL", "fullyaliveretreat@gmail.com")

# Google Analytics 4 measurement ID (G-XXXXXXXXXX). Analytics is omitted when unset.
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "registration": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # Payment events are always recorded, regardless of the global level.
        "registration.payments": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
