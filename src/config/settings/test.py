from decouple import config

from .base import *

DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="test_db"),
        "USER": config("DB_USER", default="test_user"),
        "PASSWORD": config("DB_PASSWORD", default="test_pass"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}
