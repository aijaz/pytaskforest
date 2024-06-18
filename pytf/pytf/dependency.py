import datetime

import pytz
from attrs import define

from pytf.pytf.config import Config
from pytf.pytf.dirs import (
    todays_family_dir,
    todays_log_dir,
)
from pytf.pytf.mockdatetime import MockDateTime


@define
class Dependency:
    config: Config

    def met(self) -> bool:
        return False


@define
class TimeDependency(Dependency):
    hh: int
    mm: int
    tz: str

    def met(self) -> bool:
        now = MockDateTime.now(self.tz)
        then = datetime.datetime(now.year, now.month, now.day, self.hh, self.mm, 0, 0, pytz.timezone(self.tz))
        return then <= now


@define
class JobDependency(Dependency):
    family_name: str
    job_name: str

    def met(self) -> bool:
        # Get job, find out from status if job has run today - need to get status
        family_dir = todays_family_dir(config=self.config)
        log_dir = todays_log_dir(config=self.config)
        return True


@define
class TokenDependency(Dependency):

    def met(self) -> bool:
        return True
