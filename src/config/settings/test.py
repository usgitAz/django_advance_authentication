import os

from .base import *

DEBUG = True
SECRET_KEY = "django-insecure-test-key"
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_db",
        "USER": "test_user",
        "PASSWORD": "test_pass",
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": 5432,
    }
}
