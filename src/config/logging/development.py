from .base import LOGGING

LOGGING["handlers"]["console"].update(
    {
        "level": "DEBUG",
    }
)

LOGGING["loggers"][""]["handlers"] = ["console"]
LOGGING["loggers"][""]["level"] = "DEBUG"

LOGGING["loggers"]["django.request"] = {
    "handlers": ["console"],
    "level": "DEBUG",
    "propagate": False,
}

LOGGING["loggers"]["django.server"] = {
    "handlers": ["console"],
    "level": "DEBUG",
    "propagate": False,
}

LOGGING["loggers"]["apps"]["handlers"] = ["console"]
LOGGING["loggers"]["apps"]["level"] = "DEBUG"
