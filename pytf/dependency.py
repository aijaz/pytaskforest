import datetime

import pytz
from attrs import define

from .config import Config
import pytf.dirs as dirs
from .mockdatetime import MockDateTime


@define
class Dependency:
    config: Config

    def met(self, user_info) -> bool:
        return False


@define
class TimeDependency(Dependency):
    hh: int
    mm: int
    tz: str

    def met(self, _=None) -> bool:
        now = MockDateTime.now(self.tz)
        then = pytz.timezone(self.tz).localize(datetime.datetime(now.year, now.month, now.day, self.hh, self.mm, 0, 0))
        return then <= now


@define
class JobDependency(Dependency):
    family_name: str
    job_name: str

    def met(self, user_info) -> bool:
        # Get job, find out from status if job has run today - need to get status
        logged_jobs_dict = user_info
        if family_dict := logged_jobs_dict.get(self.family_name):
            return family_dict.get(self.job_name) is not None
        return False


@define
class TokenDependency(Dependency):

    def met(self, user_info) -> bool:
        return True
