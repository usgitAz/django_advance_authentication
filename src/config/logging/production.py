import copy

import structlog

from .base import BASE_LOGGING

LOGGING = copy.deepcopy(BASE_LOGGING)

LOGGING["formatters"]["json_console"] = {
    "()": "structlog.stdlib.ProcessorFormatter",
    "processor": structlog.processors.JSONRenderer(),
    "foreign_pre_chain": [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ],
}

LOGGING["handlers"]["console"]["formatter"] = "json_console"

LOGGING["handlers"].pop("file", None)
LOGGING["root"]["handlers"] = ["console"]
