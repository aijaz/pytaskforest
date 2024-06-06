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


@define
class Job:
    job_name: str
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

        # convert true, false to lowercase
        patterns = ((re.compile('(= *)TRUE\\b', flags=re.IGNORECASE), '= true'), (re.compile('(= *)FALSE\\b', flags=re.IGNORECASE), '= false'))
        for pattern, repl in patterns:
            inner_data = re.sub(pattern, repl, inner_data)

        toml_str = f' d = {{ {inner_data} }}'

        try:
            toml_d = tomlkit.loads(toml_str)
        except tomlkit.exceptions.UnexpectedCharError as e:
            raise PyTaskforestParseException(MSG_INNER_PARSING_FAILED) from e

        d = toml_d.get('d', {})

        cls.validate_inner_params(d, j.job_name)

        j.start_time_hr, j.start_time_min = cls.parse_time(d, j, 'start', MSG_START_TIME_PARSING_FAILED)
        j.until_hr, j.until_min = cls.parse_time(d, j, 'until', MSG_UNTIL_TIME_PARSING_FAILED)
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
    def parse_time(cls, d, j, field_name, exception_str) -> (int | None, int | None):
        if val := d.get(field_name):
            if len(val) != 4:
                raise PyTaskforestParseException(f"{exception_str} {j.job_name}")
            try:
                hh, mm = (int(val[:2]), int(val[2:]))
            except ValueError as e:
                raise PyTaskforestParseException(
                    f"{exception_str} {j.job_name}"
                ) from e
            return hh, mm

        return None, None

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
                raise (PyTaskforestParseException(f"{MSG_UNRECOGNIZED_PARAM}: {job_name}"))

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

        def simple_type(i) -> str:
            if type(i) is tomlkit.items.String:
                return 'str'
            elif type(i) is tomlkit.items.Integer:
                return 'int'
            elif type(i) is bool:
                return 'bool'
            else:
                return type(i)

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
