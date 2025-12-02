from .base import LOGGING

LOGGING["handlers"]["console"] = {
    "class": "logging.StreamHandler",
    "stream": "ext://sys.stdout",
    "formatter": "json",
    "level": "INFO",
}
LOGGING["loggers"][""] = {
    "handlers": ["console", "file_app", "file_error", "file_json", "file_security"],
    "level": "INFO",
    "propagate": False,
}
LOGGING["loggers"]["apps"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "ERROR"
