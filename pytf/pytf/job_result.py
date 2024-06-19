import datetime

from attrs import define, field

from .job_status import JobStatus

@define
class JobResult:
    family_name: str
    job_name: str
    tz: str
    status: JobStatus
    queue_name: str
    worker_name: str
    start_time: datetime.datetime|None = field(default=None)
    error_code: int|None = field(default=None)
