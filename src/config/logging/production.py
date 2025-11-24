from .base import LOGGING

LOGGING["handlers"]["console"] = {
    "class": "logging.StreamHandler",
    "formatter": "json",
    "level": "INFO",
}

LOGGING["loggers"][""]["handlers"] = ["console", "file_json", "file_error"]
LOGGING["loggers"][""]["level"] = "INFO"
LOGGING["loggers"]["apps"]["level"] = "INFO"
