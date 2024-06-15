import logging

import tomlkit
import tomlkit.exceptions
from attrs import define, field

from .token import Token


@define
class Config():
    toml_str: str = field(init=True)
    d = field(init=False, default={})

    log_dir: str | None = field(default=None)
    family_dir: str | None = field(default=None)
    job_dir: str | None = field(default=None)
    instructions_dir: str | None = field(default=None)
    run_wrapper: str | None = field(default=None)

    calendar_dir: str | None = field(default=None)
    wait_time: int | None = field(default=60)
    end_time_hr: int | None = field(default=23)
    end_time_min: int | None = field(default=55)
    once_only: bool = field(default=False)
    collapse: bool = field(default=True)
    chained: bool = field(default=True)
    log_level: int | None = field(default=logging.WARN)
    ignore_regex: [str] = field(default=["~$", ".bak$", "\\$$"])
    tokens: [Token] = field(default=None)
    num_retries: int = field(default=1)
    retry_sleep: int = field(default=300)


    def __getitem__(self, item):
        return self.d[item]

    @classmethod
    def from_str(cls, toml_str):
        try:
            d = tomlkit.loads(toml_str)
            obj = cls(toml_str=toml_str)
            obj.d = d
            return obj
        except tomlkit.exceptions.UnexpectedCharError as e:
            return cls("")
