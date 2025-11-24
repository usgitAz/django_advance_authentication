import sys

log_format = "%(asctime)s %(levelname)s %(name)s %(message)s %(process)d %(thread)d"

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": log_format,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json",
        },
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "CRITICAL",
            "handlers": [],
            "propagate": False,
        },
    },
}

bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"

loglevel = "info"
accesslog = None  # access log set to offf
access_log_format = None
errorlog = "-"
