from enum import Enum
import re

import tomlkit
import tomlkit.exceptions
import tomlkit.items
from attrs import define, field

from .exceptions import (PyTaskforestParseException,
                         MSG_INNER_PARSING_FAILED,
                         MSG_START_TIME_PARSING_FAILED,
                         MSG_UNTIL_TIME_PARSING_FAILED,
                         MSG_UNRECOGNIZED_PARAM,
                         MSG_INVALID_TYPE,
                         )
from .parse_utils import parse_time, lower_true_false, simple_type
from pytf.pytf.dependency import Dependency


class JobStatus(Enum):
    WAITING = 1
    READY = 2
    TOKEN_WAIT = 3
    RUNNING = 4
    SUCCESS = 5
    FAILURE = 6


@define
class Job:
    job_name: str
    script: str | None = field(default=None)
    start_time_hr: int | None = field(default=None)
    start_time_min: int | None = field(default=None)
    tz: str | None = field(default=None)
    every: int | None = field(default=None)
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
    comment: str | None = field(default=None)

    # dynamic fields
    start_time_met_today: bool = field(default=False)
    family_name: str = field(default="")
    base_name: str = field(default="")
    has_actual_start: bool = field(default=False)
    status: JobStatus = field(default=JobStatus.WAITING)
    dependencies = [Dependency]



    @classmethod
    def parse(cls, job_string: str):
        j = cls(
            job_name=""
        )
        pattern = re.compile('([0-9A-Za-z_]+)\\((.*)\\)')
        match = pattern.match(job_string)
        j.job_name = match[1]

        inner_data = match[2]
        if not inner_data:
            return j

        # convert true, false to lowercase
        inner_data = lower_true_false(inner_data)

        toml_str = f' d = {{ {inner_data} }}'

        try:
            toml_d = tomlkit.loads(toml_str)
        except tomlkit.exceptions.UnexpectedCharError as e:
            raise PyTaskforestParseException(MSG_INNER_PARSING_FAILED) from e

        d = toml_d.get('d', {})

        cls.validate_inner_params(d, j.job_name)

        j.start_time_hr, j.start_time_min = parse_time(d, j.job_name, 'start', MSG_START_TIME_PARSING_FAILED)
        j.until_hr, j.until_min = parse_time(d, j.job_name, 'until', MSG_UNTIL_TIME_PARSING_FAILED)
        j.tz = d.get('tz')
        j.every = d.get('every')
        j.chained = d.get('chained')
        j.token = d.get('token')
        j.num_retries = d.get('num_retries')
        j.retry_sleep_min = d.get('retry_sleep_min')
        j.queue = d.get('queue')
        j.email = d.get('email')
        j.retry_email = d.get('retry_email')
        j.retry_success_email = d.get('retry_success-email')
        j.no_retry_email = d.get('no_retry_email')
        j.no_retry_success_email = d.get('no_retry_success_email')
        j.comment = d.get('comment')

        return j

    @classmethod
    def validate_inner_params(cls, d, job_name):
        valid_keys = [
            'start',
            'until',
            'tz',
            'every',
            'chained',
            'token',
            'num_retries',
            'retry_sleep_min',
            'queue',
            'email',
            'retry_email',
            'retry_success-email',
            'no_retry_email',
            'no_retry_success_email',
            'comment',
        ]
        for key in d:
            if key not in valid_keys:
                raise (PyTaskforestParseException(f"{MSG_UNRECOGNIZED_PARAM}: {job_name}/{key}"))

        strs = [
            'tz',
            'queue',
            'email',
            'retry_email',
            'retry_success-email',
            'comment',
        ]

        ints = [
            'every',
            'num_retries',
            'retry_sleep_min',
        ]

        bools = [
            'chained',
            'no_retry_email',
            'no_retry_success_email',
        ]

        str_lists = [
            'token',
        ]

        for key in strs:
            if key in d and type(d[key]) is not tomlkit.items.String:
                raise PyTaskforestParseException(f"{MSG_INVALID_TYPE} {job_name}/{key} ({d[key]}) is type {simple_type(d[key])}")

        for key in ints:
            if key in d and type(d[key]) is not tomlkit.items.Integer:
                raise PyTaskforestParseException(f"{MSG_INVALID_TYPE} {job_name}/{key} ({d[key]}) is type {simple_type(d[key])}")

        for key in bools:
            if key in d and type(d[key]) is not bool:
                raise PyTaskforestParseException(f"{MSG_INVALID_TYPE} {job_name}/{key} ({d[key]}) is type {simple_type(d[key])}")

        for key in str_lists:
            if key in d:
                for i in d[key]:
                    if type(i) is not tomlkit.items.String:
                        raise PyTaskforestParseException(f"{MSG_INVALID_TYPE} {job_name}/{key} ({d[key]} :: {i})")
