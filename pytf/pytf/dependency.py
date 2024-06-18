import datetime

import pytz
from attrs import define

from pytf.pytf.config import Config
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
        then = datetime.datetime(now.year, now.month, now.day, self.hr, self.mm, 0, 0, pytz.timezone(self.tz))
        return then <= now


@define
class JobDependency(Dependency):
    family_name: str
    job_name: str

    def met(self) -> bool:
        # Get job, find out from status if job has run today - need to get status
        return True


@define
class TokenDependency(Dependency):

    def met(self) -> bool:
        return True
