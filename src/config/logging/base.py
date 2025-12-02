from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = {
    "fmt": "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
}

JSON_LOG_FORMAT = (
    '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
    '"module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, '
    '"message": %(message)s, "process": %(process)d, "thread": %(thread)d}'
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": LOG_FORMAT["fmt"],
            "datefmt": LOG_FORMAT["datefmt"],
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": JSON_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "INFO",
        },
        "file_app": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "verbose",
            "level": "INFO",
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
            "level": "WARNING",
        },
        "file_security": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "security.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
            "level": "INFO",
        },
        "file_json": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.json.log",
            "maxBytes": 50 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "json",
            "level": "INFO",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file_app", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console", "file_app"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["file_security"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file_app"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
