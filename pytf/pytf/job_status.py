from enum import Enum


class JobStatus(Enum):
    WAITING = 1
    READY = 2
    TOKEN_WAIT = 3
    RUNNING = 4
    SUCCESS = 5
    FAILURE = 6

