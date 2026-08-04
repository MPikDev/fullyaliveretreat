"""Settings used by the test suite.

Run with:  python manage.py test --settings=personal_code.settings_test

Overrides the pieces of production configuration that make tests slow or that
require infrastructure the suite should not depend on.
"""

import os

os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("PAYPAL_ENDPOINT", "test-ipn-endpoint")
# Force SQLite regardless of any DATABASE_URL in the developer's environment.
os.environ.pop("DATABASE_URL", None)

from personal_code.settings import *  # noqa: F401,F403,E402

# The manifest storage requires a collectstatic run; tests don't need hashing.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Fast, deterministic password hashing.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Lockout behaviour is exercised explicitly; leave it off by default so that
# unrelated tests logging in repeatedly don't trip it.
AXES_ENABLED = False

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Never reach the network from a test.
FAR_EMAIL_APP_PASSWORD = ""

SECURE_SSL_REDIRECT = False

LOGGING["root"]["level"] = "CRITICAL"  # noqa: F405
for _logger in LOGGING["loggers"].values():  # noqa: F405
    _logger["level"] = "CRITICAL"
    _logger["handlers"] = ["console"]
