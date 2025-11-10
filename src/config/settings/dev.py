from .base import (
    ALLOWED_HOSTS,
    BASE_DIR,
    DATABASES,
    DEBUG,
)

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
