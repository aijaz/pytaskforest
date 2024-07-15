import logging

import tomlkit
import tomlkit.exceptions
from attrs import define, field

import pytf.exceptions as ex
from pytf.pytftoken import PyTfToken


@define
class Config:
    toml_str: str = field(init=True)
    d = field(init=False)

    @d.default
    def _d_default(self):
        return {}

    run_local: bool = field(default=False)
    log_dir: str | None = field(default=None)
    family_dir: str | None = field(default=None)
    job_dir: str | None = field(default=None)
    instructions_dir: str | None = field(default=None)
    todays_log_dir: str | None = field(default=None)
    todays_family_dir: str | None = field(default=None)

    end_time_hr: int | None = field(default=23)
    end_time_min: int | None = field(default=55)
    once_only: bool = field(default=False)
    collapse: bool = field(default=True)
    chained: bool = field(default=True)
    log_level: int | None = field(default=logging.WARN)
    ignore_regex: [str] = field()

    @ignore_regex.default
    def _ignore_regex_default(self):
        return [".*~$", ".*\\.bak$", ".*\\$$"]

    tokens: [PyTfToken] = field(default=[])
    tokens_by_name: dict = field(default={})
    num_retries: int = field(default=0)
    retry_sleep: int = field(default=1)
    web_hook: str = field(default=None)
    hook_auth: str = field(default=None)
    primary_tz: str = field(default="UTC")
    calendars: dict = field(default={})

    def set_if_not_none(self, key, orig_value):
        return self.d[key] if self.d.get(key) is not None else orig_value

    @classmethod
    def from_str(cls, toml_str):
        try:
            d = tomlkit.loads(toml_str)
            obj = cls(toml_str=toml_str)
            obj.d = d
            obj.log_dir = obj.set_if_not_none('log_dir', obj.log_dir)
            obj.family_dir = obj.set_if_not_none('family_dir', obj.family_dir)
            obj.job_dir = obj.set_if_not_none('job_dir', obj.job_dir)
            obj.instructions_dir = obj.set_if_not_none('instructions_dir', obj.instructions_dir)
            obj.end_time_hr = obj.set_if_not_none('end_time_hr', obj.end_time_hr)
            obj.end_time_min = obj.set_if_not_none('end_time_min', obj.end_time_min)
            obj.collapse = obj.set_if_not_none('collapse', obj.collapse)
            obj.chained = obj.set_if_not_none('chained', obj.chained)
            obj.log_level = obj.set_if_not_none('log_level', obj.log_level)  # TODO: Convert this from string to proper type
            obj.ignore_regex = obj.set_if_not_none('ignore_regex', obj.ignore_regex)
            obj.num_retries = obj.set_if_not_none('num_retries', obj.num_retries)
            obj.retry_sleep = obj.set_if_not_none('retry_sleep', obj.retry_sleep)
            obj.web_hook = obj.set_if_not_none('web_hook', obj.web_hook)
            obj.hook_auth = obj.set_if_not_none('hook_auth', obj.hook_auth)
            obj.primary_tz = obj.set_if_not_none('primary_tz', obj.primary_tz)
            obj.run_local = obj.set_if_not_none('run_local', obj.run_local)
            obj.once_only = obj.set_if_not_none('once_only', obj.once_only)
            obj.calendars = obj.set_if_not_none('calendars', obj.calendars)

            if temp_tokens := obj.set_if_not_none('tokens', obj.tokens):
                obj.tokens = [
                    PyTfToken(k, v)
                    for k, v in temp_tokens.items()
                ]
                for tok in obj.tokens:
                    obj.tokens_by_name[tok.name] = tok

            return obj
        except tomlkit.exceptions.UnexpectedCharError as e:
            raise ex.PyTaskforestParseException(ex.MSG_CONFIG_PARSING_FAILED) from e
        except tomlkit.exceptions.UnexpectedEofError as e:
            raise ex.PyTaskforestParseException(ex.MSG_CONFIG_PARSING_FAILED) from e
