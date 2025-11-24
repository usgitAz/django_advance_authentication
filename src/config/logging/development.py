from .base import LOGGING

LOGGING["handlers"]["console"] = {
    "class": "logging.StreamHandler",
    "formatter": "json",
    "level": "INFO",
}

LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["loggers"][""]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"
