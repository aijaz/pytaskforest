from enum import Enum


class JobStatus(Enum):
    WAITING = "Waiting"
    READY = "Ready"
    RELEASED = "Released"
    TOKEN_WAIT = "Token Wait"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILURE = "Failure"
    HOLD = "On Hold"
