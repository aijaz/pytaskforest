import datetime

from attrs import define, field

from .job_status import JobStatus


@define
class JobResult:
    family_name: str
    job_name: str
    status: JobStatus
    queue_name: str
    tz: str | None = field(default=None)
    worker_name: str | None = field(default=None)
    start_time: str | None = field(default=None)  # this comes in from parsing a string from .info
    error_code: int | None = field(default=None)
    tokens: [str] = field(default=[])

    
def serializer(_, field, value):
    if  isinstance(value, JobStatus):
        return value.value
    elif isinstance(value, list):
        return list(value)
    return value
