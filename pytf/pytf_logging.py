import logging
import logging.config
import os


def setup_logging(log_dir: str):
    logging_dict = get_logging_config(log_dir)
    logging.config.dictConfig(logging_dict)
    # _ = logging.getLogger('runner')


def get_logging_config(log_dir: str):

    # if not os.path.exists("/pytf_root/logs/pytf.log"):
    #     print("**** Creating log file")
    #     open("/pytf_root/logs/pytf.log", 'a').close()  # create empty log file
    #     # via https://stackoverflow.com/a/74059469

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s %(module)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "detailed": {
                "format": "%(asctime)s %(module)s:%(lineno)d %(levelname)s %(message)s",
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
                "level": "INFO",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": os.path.join(log_dir, "pytf.log"),
                "maxBytes": 10_000_000,
                "backupCount": 10,
            },
            "json": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": os.path.join(log_dir, "pytf.jlog"),
                "maxBytes": 10_000_000,
                "backupCount": 2,
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["console", "file", "json"]
            }
        }
    }


