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

    def __str__(self):
        return ""

    def __hash__(self):
        return hash(str(self))

    def __eq__(self,other):
        return str(self) == str(other)


@define
class TimeDependency(Dependency):
    hh: int
    mm: int
    tz: str

    def met(self, _=None) -> bool:
        now = MockDateTime.now(self.tz)
        then = pytz.timezone(self.tz).localize(datetime.datetime(now.year, now.month, now.day, self.hh, self.mm, 0, 0))
        return then <= now

    def __str__(self):
        return f"{self.hh}{self.mm}{self.tz}"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


@define
class JobDependency(Dependency):
    family_name: str
    job_name: str

    def met(self, user_info) -> bool:
        # Get job, find out from status if job has run today - need to get status
        logged_jobs_dict = user_info
        if family_dict := logged_jobs_dict.get(self.family_name):
            if family_dict.get(self.job_name) is None:
                return False
            if family_dict[self.job_name].error_code is None:
                return False
            return family_dict[self.job_name].error_code == 0
        return False

    def __str__(self):
        return f"{self.family_name}{self.job_name}"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self,other):
        return str(self) == str(other)


@define
class TokenDependency(Dependency):

    def met(self, user_info) -> bool:
        return True
