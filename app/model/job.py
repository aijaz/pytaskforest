import re

import tomlkit
import tomlkit.exceptions
from attrs import define, field

from .exceptions import (PyTaskforestParseException,
                         MSG_INNER_PARSING_FAILED,
                         MSG_START_TIME_PARSING_FAILED,
                         )


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
        pattern = re.compile('([0-9A-Za-z_]+)\((.*)\)')
        match = pattern.match(job_string)
        j.job_name = match[1]

        inner_data = match[2]
        if not inner_data:
            return j

        toml_str = f' d = {{ {inner_data} }}'

        try:
            toml_d = tomlkit.loads(toml_str)
        except tomlkit.exceptions.UnexpectedCharError as e:
            raise PyTaskforestParseException(MSG_INNER_PARSING_FAILED) from e

        d = toml_d.get('d', {})

        if start := d.get('start'):
            if len(start) != 4:
                raise PyTaskforestParseException(f"{MSG_START_TIME_PARSING_FAILED} {j.job_name}")
            try:
                j.start_time_hr, j.start_time_min = (int(start[:2]), int(start[2:]))
            except ValueError as e:
                raise PyTaskforestParseException(
                    f"{MSG_START_TIME_PARSING_FAILED} {j.job_name}"
                ) from e

        return j
