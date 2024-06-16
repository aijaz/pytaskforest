import datetime
import logging
from logging.config import dictConfig
import os
import sys


def setup_logging():
    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            'stdout_handler': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': sys.stdout,
                'level': 'INFO'
            }

        },
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

