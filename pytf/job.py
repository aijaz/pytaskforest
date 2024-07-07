import re

import tomlkit
import tomlkit.exceptions
import tomlkit.items
from attrs import define, field

import pytf.exceptions as ex
from .parse_utils import parse_time, lower_true_false, simple_type
from .dependency import Dependency
from .job_status import JobStatus


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
    tokens: list[str] | None = field(default=None)
    num_retries: int | None = field(default=None)
    retry_sleep_min: int | None = field(default=None)
    queue: str | None = field(default="default")
    email: str | None = field(default=None)
    retry_email: str | None = field(default=None)
    retry_success_email: str | None = field(default=None)
    no_retry_email: bool | None = field(default=None)
    no_retry_success_email: bool | None = field(default=None)
    comment: str | None = field(default=None)

    # dynamic fields
    start_time_met_today: bool = field(default=False)
    family_name: str|None = field(default=None)
    base_name: str = field(default="")
    has_actual_start: bool = field(default=False)
    status: JobStatus = field(default=JobStatus.WAITING)
    dependencies: [Dependency] = field()

    @dependencies.default
    def _dependencies_default(self):
        return set()

    @classmethod
    def parse(cls, job_string: str, family_name: str):
        j = cls(
            job_name="",
            family_name=family_name
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
            raise ex.PyTaskforestParseException(ex.MSG_INNER_PARSING_FAILED) from e

        d = toml_d.get('d', {})

        cls.validate_inner_params(d, j.job_name)

        j.start_time_hr, j.start_time_min = parse_time(d, j.job_name, 'start', ex.MSG_START_TIME_PARSING_FAILED)
        j.until_hr, j.until_min = parse_time(d, j.job_name, 'until', ex.MSG_UNTIL_TIME_PARSING_FAILED)
        j.tz = d.get('tz')
        j.every = d.get('every')
        j.chained = d.get('chained')
        j.tokens = d.get('tokens')
        j.num_retries = d.get('num_retries')
        j.retry_sleep_min = d.get('retry_sleep_min')
        j.queue = d.get('queue', 'default')
        j.email = d.get('email')
        j.retry_email = d.get('retry_email')
        j.retry_success_email = d.get('retry_success-email')
        j.no_retry_email = d.get('no_retry_email')
        j.no_retry_success_email = d.get('no_retry_success_email')
        j.comment = d.get('comment')

        return j

    @classmethod
    def validate_inner_params(cls, d, job_name):
        cls.validate_keys(d, job_name)

        cls.validate_strs(d, job_name)

        cls.validate_ints(d, job_name)

        cls.validate_bools(d, job_name)

        cls.validate_str_lists(d, job_name)

    @classmethod
    def validate_str_lists(cls, d, job_name):
        str_lists = [
            'tokens',
        ]
        for key in [k for k in str_lists if k in d]:
            for i in d[key]:
                if type(i) is not tomlkit.items.String:
                    raise ex.PyTaskforestParseException(f"{ex.MSG_INVALID_TYPE} {job_name}/{key} ({d[key]} :: {i})")

    @classmethod
    def validate_bools(cls, d, job_name):
        bools = [
            'chained',
            'no_retry_email',
            'no_retry_success_email',
        ]
        for key in bools:
            if key in d and type(d[key]) is not bool:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_INVALID_TYPE} {job_name}/{key} ({d[key]}) is type {simple_type(d[key])}")

    @classmethod
    def validate_strs(cls, d, job_name):
        strs = [
            'tz',
            'queue',
            'email',
            'retry_email',
            'retry_success-email',
            'comment',
        ]
        for key in strs:
            if key in d and type(d[key]) is not tomlkit.items.String:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_INVALID_TYPE} {job_name}/{key} ({d[key]}) is type {simple_type(d[key])}")

    @classmethod
    def validate_ints(cls, d, job_name):
        ints = [
            'every',
            'num_retries',
            'retry_sleep_min',
        ]
        for key in ints:
            if key in d and type(d[key]) is not tomlkit.items.Integer:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_INVALID_TYPE} {job_name}/{key} ({d[key]}) is type {simple_type(d[key])}")

    @classmethod
    def validate_keys(cls, d, job_name):
        valid_keys = [
            'start',
            'until',
            'tz',
            'every',
            'chained',
            'tokens',
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
                raise (ex.PyTaskforestParseException(f"{ex.MSG_UNRECOGNIZED_PARAM}: {job_name}/{key}"))
