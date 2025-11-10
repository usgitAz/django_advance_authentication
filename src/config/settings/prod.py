from .base import (
    ALLOWED_HOSTS,
    CSRF_COOKIE_SECURE,
    DATABASES,
    DEBUG,
    SECURE_BROWSER_XSS_FILTER,
    SECURE_CONTENT_TYPE_NOSNIFF,
    SECURE_SSL_REDIRECT,
    SESSION_COOKIE_SECURE,
    config,
)

# Security settings
DEBUG = False
ALLOWED_HOSTS = ["http://127.0.0.1:8000"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

DATABASES["default"].update(
    {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
)

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
