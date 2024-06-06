import re

from attrs import define, field


@define
class Job:
    job_name: str
    start_time_hr: int | None = field(default=None)
    start_time_min: int | None = field(default=None)
    tz: str | None = field(default=None)
    every: str | None = field(default=None)
    until_hr: int | None = field(default=None)
    until_min: int | None = field(default=None)
    chained: bool | None = field(default=None)
    token: list[str] | None = field(default=None)
    num_retries: int | None = field(default=None)
    retry_sleep_min: int | None = field(default=None)
    queue: str | None = field(default=None)
    email: str | None = field(default=None)
    retry_email: str | None = field(default=None)
    retry_success_email: str | None = field(default=None)
    no_retry_email: bool | None = field(default=None)
    no_retry_success_email: bool | None = field(default=None)

    @classmethod
    def parse(cls, job_string: str):
        j = cls(
            job_name=""
        )
        pattern = re.compile('([0-9A-Za-z_])+\((.*)\)')
        match = pattern.match(job_string)
        j.job_name = match[1]
        return j
