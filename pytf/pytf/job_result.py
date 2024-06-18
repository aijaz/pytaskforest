import datetime

from attrs import define, field

from pytf.pytf.job_status import JobStatus

@define
class JobResult:
    family_name: str
    job_name: str
    status: JobStatus
    tz: str
    start_time: datetime.datetime|None = field(default=None)
