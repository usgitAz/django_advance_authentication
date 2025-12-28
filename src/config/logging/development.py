import copy

import structlog

from .base import BASE_LOGGING

LOGGING = copy.deepcopy(BASE_LOGGING)

LOGGING["formatters"]["colored_console"] = {
    "()": "structlog.stdlib.ProcessorFormatter",
    "processor": structlog.dev.ConsoleRenderer(
        colors=True,
        pad_event=0,
    ),
    "foreign_pre_chain": [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ],
}

LOGGING["handlers"]["console"]["formatter"] = "colored_console"
LOGGING["handlers"]["console"]["level"] = "DEBUG"

LOGGING["formatters"]["json_file"] = {
    "()": "structlog.stdlib.ProcessorFormatter",
    "processor": structlog.processors.JSONRenderer(),
    "foreign_pre_chain": [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ],
}

LOGGING["handlers"]["file"]["formatter"] = "json_file"

LOGGING["root"]["level"] = "DEBUG"

LOGGING["loggers"]["django.server"] = {
    "handlers": [],
    "level": "WARNING",
    "propagate": False,
}

LOGGING["loggers"]["django_structlog.middlewares.request"] = {
    "handlers": [],
    "level": "WARNING",
    "propagate": False,
}

LOGGING["loggers"]["django.utils.autoreload"] = {
    "handlers": [],
    "level": "WARNING",
    "propagate": False,
}

LOGGING["loggers"]["drf_spectacular"] = {
    "handlers": [],
    "level": "WARNING",
    "propagate": False,
}
