from attrs import define, field

from .forest import Forest


@define
class Calendar:
    calendar_name: str


@define
class Days:
    days: str


@define
class Family:
    start_time_hr: int
    start_time_min: int
    tz: str
    calendar_or_days: Calendar | Days | None = field(default=None)
    queue: str | None = field(default=None)
    email: str | None = field(default=None)
    retry_email: str | None = field(default=None)
    retry_success_email: str | None = field(default=None)
    no_retry_email: bool | None = field(default=None)
    no_retry_success_email: bool | None = field(default=None)
    forests: [Forest] = field(default=None)

    @classmethod
    def parse(cls, job_string: str):
        j = cls(
            start_time_hr=0,
            start_time_min=0,
            tz=''
        )
        return j
