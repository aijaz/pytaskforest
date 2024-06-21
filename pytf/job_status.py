from enum import Enum


class JobStatus(Enum):
    WAITING = "Waiting"
    READY = "Ready"
    TOKEN_WAIT = "Token Wait"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILURE = "Failure"

