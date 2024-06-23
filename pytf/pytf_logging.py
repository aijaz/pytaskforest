import os


def get_logging_config(log_dir: str):
    filename = os.path.join(log_dir, "pytf.log.jsonl")
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s %(module)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "detailed": {
                "format": "%(asctime)s %(module)s:%(linenum)d %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "json": {
                "()": "pytf.pytf_json_formatter.PytfJSONFormatter",
                "fmt_keys": {
                    "level": "levelname",
                    "message": "message",
                    "timestamp": "timestamp",
                    "logger": "name",
                    "module": "module",
                    "function": "funcName",
                    "line": "lineno",
                    "thread_name": "threadName"
                }
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json",
                "filename": filename,
                "maxBytes": 10000000,
                "backupCount": 10,
            },
            "queue_handler": {
                "class": "logging.handlers.QueueHandler",
                "handlers": ["console", "file"],
                "respect_handler_level": True,
                "comments": "view https://www.youtube.com/watch?v=9L77QExPmI0 for notes on this"
            }
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["console", "file"]
            }
        }
    }


